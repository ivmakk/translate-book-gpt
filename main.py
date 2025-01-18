import html
import langcodes
import tiktoken
import argparse, \
       re, \
       yaml

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from openai import OpenAI

## VS Code Debugging
# import ptvsd
#
# # Allow other computers to attach to ptvsd at this IP address and port.
# #
# # netstat -ano | findstr :5678
# # taskkill /PID <PID> /F
# #
# # OR
# #
# # Stop-Process -Id (Get-NetTCPConnection -LocalPort 5678).OwningProcess -Force
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)

# # Pause the program until a remote debugger is attached
# print("Waiting for debugger to attach...")
# ptvsd.wait_for_attach()

GPT_MODEL_NAME = 'gpt-4o-mini'

def read_config(config_file):
    with open(config_file, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    return config


def split_html_by_sentence(html_str, max_chunk_size=10000):
    sentences = html_str.split('. ')

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) > max_chunk_size:
            chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += '. '
            current_chunk += sentence
    
    if current_chunk:
        chunks.append(current_chunk)

    # Remove dot from the beginning of first chunk
    chunks[0] = chunks[0][2:]

    # Add dot to the end of each chunk
    for i in range(len(chunks)):
        chunks[i] += '.'

    return chunks

def split_html_by_newline(html_str, max_chunk_size=10000):
    chunks = []
    lines = html_str.split('\n')

    if len(html_str) == 0:
        return chunks

    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += '\n'
            current_chunk += line
    
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def system_prompt(from_lang, to_lang):
    p  = "You are an %s-to-%s translator. " % (from_lang, to_lang)
    p += "Keep all special characters and HTML tags as in the source text. Return only %s translation." % to_lang
    return p


def translate_chunk(client, text, from_lang='EN', to_lang='PL'):
    response = client.chat.completions.create(
        model=GPT_MODEL_NAME,
        temperature=0.2,
        messages=[
            { 'role': 'developer', 'content': system_prompt(from_lang, to_lang) },
            { 'role': 'user', 'content':  html.escape(text) },
        ]
    )

    translated_text = response.choices[0].message.content
    decoded_text = html.unescape(translated_text)

    original_lines = text.count('\n')
    decoded_lines = decoded_text.count('\n')

    if abs(original_lines - decoded_lines) > 1:
        print("Warning: The number of lines in the original text (%d) and the decoded text (%d) are different." % (original_lines, decoded_lines))

    return decoded_text


def translate_toc(client, toc, from_lang='EN', to_lang='PL'):
    toc_list = list(toc)
    toc_text = "\n".join([item.title.strip() for item in toc_list if isinstance(item, epub.Link)])
    
    translated_toc_text = translate_text(client, toc_text, from_lang, to_lang)
    translated_titles = [title.strip() for title in translated_toc_text.split('\n')]
    
    translated_toc = []
    title_index = 0
    for item in toc_list:
        if isinstance(item, epub.Link):
            translated_toc.append(epub.Link(item.href, translated_titles[title_index], item.uid))
            title_index += 1
        else:
            translated_toc.append(item)
    
    return tuple(translated_toc)

def translate_text(client, text, from_lang='EN', to_lang='PL'):
    translated_chunks = []
    chunks = split_html_by_newline(text)

    for i, chunk in enumerate(chunks):
        print("\tTranslating chunk %d/%d..." % (i+1, len(chunks)))
        translated_chunks.append(translate_chunk(client, chunk, from_lang, to_lang))

    return ' '.join(translated_chunks)


def translate(client, input_epub_path, output_epub_path, from_chapter=0, to_chapter=9999, from_lang='EN', to_lang='PL'):
    book = epub.read_epub(input_epub_path)

    book.set_unique_metadata('DC', 'language', langcodes.standardize_tag(to_lang))

    current_chapter = 1
    chapters_count = len([i for i in book.get_items() if i.get_type() == ebooklib.ITEM_DOCUMENT])

    book.toc = translate_toc(client, book.toc, from_lang, to_lang)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            if current_chapter >= from_chapter and current_chapter <= to_chapter:
                print("Processing chapter %d/%d..." % (current_chapter, chapters_count))
                soup = BeautifulSoup(item.content, 'html.parser')
                translated_text = translate_text(client, str(soup), from_lang, to_lang)

                soup.body.clear()
                translated_soup = BeautifulSoup(translated_text, 'html.parser')
                soup.body.extend(translated_soup.body.contents)

                if soup.title and translated_soup.title:
                    soup.title.string = translated_soup.title.string

                item.content = str(soup).encode('utf-8')

            current_chapter += 1

    epub.write_epub(output_epub_path, book, {})


def show_chunks(input_epub_path):
    book = epub.read_epub(input_epub_path)

    encoding = tiktoken.encoding_for_model(GPT_MODEL_NAME)

    book_total_tokens = 0
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            content_str = str(BeautifulSoup(item.content, 'html.parser'))
            chunks = split_html_by_newline(content_str)

            print("Document: %s" % item.get_name())
            
            document_total_tokens = 0
            for i, chunk in enumerate(chunks):
                tokens = encoding.encode(chunk)
                print("Chunk %d/%d (Tokens: %d):" % (i+1, len(chunks), len(tokens)))

                document_total_tokens += len(tokens)
                
                lines = chunk.split('\n')
                if len(lines) > 6:
                    print('\n'.join(lines[:3]) + "\n...\n" + '\n'.join(lines[-3:]) + "\n\n")
                else:
                    print('\n'.join(lines) + "\n\n")

                book_total_tokens += document_total_tokens

            print("Total tokens in document: %d\n" % document_total_tokens)

            input_price = calculate_input_price(document_total_tokens, GPT_MODEL_NAME)
            output_price = calculate_output_price(document_total_tokens, GPT_MODEL_NAME)
            total_price = input_price + output_price
            print("Price for input: $%.2f, Price for output: $%.2f, Total price: $%.2f" % (input_price, output_price, total_price))
            
            print("--------------------------------------------------\n")

    input_price = calculate_input_price(book_total_tokens, GPT_MODEL_NAME)
    output_price = calculate_output_price(book_total_tokens, GPT_MODEL_NAME)
    total_price = input_price + output_price
    print("Total book price for input: $%.2f, Price for output: $%.2f, Total price: $%.2f" % (input_price, output_price, total_price))

def show_chapters(input_epub_path):
    book = epub.read_epub(input_epub_path)

    current_chapter = 1
    chapters_count = len([i for i in book.get_items() if i.get_type() == ebooklib.ITEM_DOCUMENT])

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            print("▶️  Chapter %d/%d (%d characters)" % (current_chapter, chapters_count, len(item.content)))
            soup = BeautifulSoup(item.content, 'html.parser')
            chapter_beginning = soup.text[0:250]
            chapter_beginning = re.sub(r'\n{2,}', '\n', chapter_beginning)
            print(chapter_beginning + "\n\n")

            current_chapter += 1

def calculate_input_price(tokens, model_name):
    """See https://openai.com/api/pricing/ for the latest pricing information."""
    model_prices_per_million = {
        'gpt-4o': 2.50,
        'gpt-4o-mini': 0.150
    }

    if model_name not in model_prices_per_million:
        return 0

    price_per_million = model_prices_per_million[model_name]
    price_per_token = price_per_million / 1_000_000

    return tokens * price_per_token

def calculate_output_price(tokens, model_name):
    """See https://openai.com/api/pricing/ for the latest pricing information."""
    model_prices_per_million = {
        'gpt-4o': 10.00,
        'gpt-4o-mini': 0.6
    }

    if model_name not in model_prices_per_million:
        return 0

    price_per_million = model_prices_per_million[model_name]
    price_per_token = price_per_million / 1_000_000

    return tokens * price_per_token


if __name__ == "__main__":
    # Create the top-level parser
    parser = argparse.ArgumentParser(description='App to translate or show chapters of a book.')
    subparsers = parser.add_subparsers(dest='mode', help='Mode of operation.')

    # Create the parser for the "translate" mode
    parser_translate = subparsers.add_parser('translate', help='Translate a book.')
    parser_translate.add_argument('--input', required=True, help='Input file path.')
    parser_translate.add_argument('--output', required=True, help='Output file path.')
    parser_translate.add_argument('--config', required=True, help='Configuration file path.')
    parser_translate.add_argument('--from-chapter', type=int, help='Starting chapter for translation.')
    parser_translate.add_argument('--to-chapter', type=int, help='Ending chapter for translation.')
    parser_translate.add_argument('--from-lang', help='Source language.', default='EN')
    parser_translate.add_argument('--to-lang', help='Target language.', default='PL')

    # Create the parser for the "show-chapters" mode
    parser_show = subparsers.add_parser('show-chapters', help='Show the list of chapters.')
    parser_show.add_argument('--input', required=True, help='Input file path.')

    # Create the parser for the "show-chunks" mode
    parser_show_chunks = subparsers.add_parser('show-chunks', help='Show the chunks of the book.')
    parser_show_chunks.add_argument('--input', required=True, help='Input file path.')

    # Parse the arguments
    args = parser.parse_args()

    # Call the appropriate function based on the mode
    if args.mode == 'translate':
        config = read_config(args.config)
        from_chapter = int(args.from_chapter or 0)
        to_chapter = int(args.to_chapter or 9999)
        from_lang = args.from_lang
        to_lang = args.to_lang
        openai_client = OpenAI(api_key=config['openai']['api_key'])

        translate(openai_client, args.input, args.output, from_chapter, to_chapter, from_lang, to_lang)

    elif args.mode == 'show-chapters':
        show_chapters(args.input)

    elif args.mode == 'show-chunks':
        show_chunks(args.input)

    else:
        parser.print_help()
