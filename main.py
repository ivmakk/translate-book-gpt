import html
import os
from dotenv import load_dotenv

load_dotenv()

from langchain.llms import BaseLLM
import langcodes
import tiktoken
import typer
import re

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from openai import OpenAI

from src.llm import extract_response_text, get_api_key, get_model
from src.llm_prompts import TRANSLATE_PROMPT
from src.llm_prompts import generate_book_info_prompt
from src.openai_utils import calculate_price
import tempfile

app = typer.Typer()

MODEL_VENDOR = os.getenv("MODEL_VENDOR", "openai")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))


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


def translate_chunk(client: BaseLLM, text, from_lang='EN', to_lang='PL', book_title=None, book_author=None, retry_num=0):
    RETRY_LIMIT = 3
    MAX_LINE_DIFF_PERCENTAGE = 0.1
    MIN_LINES_FOR_RETRY = 10

    full_from_lang = langcodes.Language.make(from_lang.lower()).display_name()
    full_to_lang = langcodes.Language.make(to_lang.lower()).display_name()

    messages = TRANSLATE_PROMPT.format_messages(
        from_lang=full_from_lang,
        to_lang=full_to_lang,
        book_details=generate_book_info_prompt(book_title, book_author),
        source_text=html.escape(text)
    )

    response = client.invoke(messages)
    print("\t\t" + str(response.usage_metadata))

    translated_text = extract_response_text(response)
    decoded_text = html.unescape(translated_text)

    original_lines = text.count('\n')
    decoded_lines = decoded_text.count('\n')

    if abs(original_lines - decoded_lines) > 1:
        print(f"Warning: The number of lines in the original text ({original_lines}) and the decoded text ({decoded_lines}) are different.")

        should_retry = (
            retry_num < RETRY_LIMIT and 
            original_lines > MIN_LINES_FOR_RETRY and 
            abs(original_lines - decoded_lines) / original_lines > MAX_LINE_DIFF_PERCENTAGE
        )

        if should_retry:
            print(f"Retrying translation... Attempt {retry_num + 1}/{RETRY_LIMIT}")
            return translate_chunk(
                client=client,
                text=text, 
                from_lang=from_lang, 
                to_lang=to_lang, 
                book_title=book_title, 
                book_author=book_author, 
                retry_num=retry_num + 1
            )

    return decoded_text


def translate_toc(client: BaseLLM, toc, from_lang='EN', to_lang='PL'):
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

def translate_text(client: BaseLLM, text, from_lang='EN', to_lang='PL', temp_dir=None, book_title=None, book_author=None):
    translated_chunks = []
    chunks = split_html_by_newline(text)

    for i, chunk in enumerate(chunks):
        print("\tTranslating chunk %d/%d..." % (i+1, len(chunks)))
        translated_chunks.append(translate_chunk(client, chunk, from_lang, to_lang, book_title, book_author))

        if temp_dir:
            with open(os.path.join(temp_dir, 'translated_text_%d.txt' % i), 'w', encoding='utf-8') as f:
                f.write(translated_chunks[-1])

    return ' '.join(translated_chunks)


def translate(client: BaseLLM, input_epub_path, output_epub_path, from_chapter=0, to_chapter=9999, from_lang='EN', to_lang='PL', toc=True):
    book = epub.read_epub(input_epub_path)

    book.set_unique_metadata('DC', 'language', langcodes.standardize_tag(to_lang))

    book_title = book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else None
    book_author = book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None

    current_chapter = 1
    chapters_count = len([i for i in book.get_items() if i.get_type() == ebooklib.ITEM_DOCUMENT])

    temp_dir = tempfile.mkdtemp()
    print("Debugging: Translated chunks will be stored in the temporary directory: %s" % temp_dir)

    prompt = TRANSLATE_PROMPT.format_messages(
        from_lang=from_lang,
        to_lang=to_lang,
        book_details=generate_book_info_prompt(book_title, book_author),
        source_text="..."
    )[0].content
    indented_prompt = '\n'.join(['\t' + line for line in prompt.split('\n')])
    print("Prompt sample: \n%s" % indented_prompt)

    if toc:
        book.toc = translate_toc(client, book.toc, from_lang, to_lang)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            if current_chapter >= from_chapter and current_chapter <= to_chapter:
                print("Processing chapter %d/%d..." % (current_chapter, chapters_count))
                soup = BeautifulSoup(item.content, 'html.parser')
                translated_text = translate_text(client, str(soup), from_lang, to_lang, temp_dir)

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

    encoding = tiktoken.encoding_for_model(MODEL_NAME)

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

            input_price = calculate_price(document_total_tokens, MODEL_NAME, 'input')
            output_price = calculate_price(document_total_tokens, MODEL_NAME, 'output')
            total_price = input_price + output_price
            print("Price for input: $%.2f, Price for output: $%.2f, Total price: $%.2f" % (input_price, output_price, total_price))
            
            print("--------------------------------------------------\n")

    input_price = calculate_price(book_total_tokens, MODEL_NAME, 'input')
    output_price = calculate_price(book_total_tokens, MODEL_NAME, 'output')
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

@app.command('translate', help="Translate the book.")
def translate_command(
    input: str = typer.Option(..., help="Input file path."),
    output: str = typer.Option(..., help="Output file path."),
    from_chapter: int = typer.Option(0, help="Starting chapter for translation."),
    to_chapter: int = typer.Option(9999, help="Ending chapter for translation."),
    from_lang: str = typer.Option('EN', help="Source language."),
    to_lang: str = typer.Option('PL', help="Target language."),
    toc: bool = typer.Option(True, is_flag=True, help="Translate the table of contents.")
):
    # client = get_model(os.getenv('OPENAI_API_KEY'), MODEL_VENDOR, MODEL_NAME, TEMPERATURE)
    client = get_model(get_api_key(MODEL_VENDOR), MODEL_VENDOR, MODEL_NAME, TEMPERATURE)
    translate(client, input, output, from_chapter, to_chapter, from_lang, to_lang, toc)

@app.command('show-chapters', help="Show the chapters of the book.")
def show_chapters_command(input: str = typer.Option(..., help="Input file path.")):
    show_chapters(input)

@app.command('show-chunks', help="Show the chunks of the book chapters and estimated prices for each.")
def show_chunks_command(input: str = typer.Option(..., help="Input file path.")):
    show_chunks(input)

if __name__ == "__main__":
    app()
