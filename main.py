import html
import json
import os
from dotenv import load_dotenv

from src.epub_utils import preserve_head_links
from src.epub_utils import get_metadata_author
from src.epub_utils import get_metadata_title
from src.glossary import extract_glossary
from src.html_utils import extract_text_from_html, minify_attributes, restore_attributes
from src.html_utils import split_html_by_newline
from src.utils import generate_book_filename
from src.utils import save_chunk_to_file
from src.utils import lang_code_to_full_lang

load_dotenv()

from langchain.llms import BaseLLM
import langcodes
import tiktoken
import typer
import re

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from src.llm import extract_response_text, get_api_key, get_model
from src.llm_prompts import TRANSLATE_PROMPT
from src.llm_prompts import generate_book_info_prompt
from src.model_prices import calculate_price
import tempfile

app = typer.Typer()

MODEL_VENDOR = os.getenv("MODEL_VENDOR", "openai")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))

MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", 10_000))


def translate_chunk(client: BaseLLM, text, from_lang, to_lang, book_title=None, book_author=None, retry_num=0):
    RETRY_LIMIT = 3
    MAX_LINE_DIFF_PERCENTAGE = 0.1
    MIN_LINES_FOR_RETRY = 10

    messages = TRANSLATE_PROMPT.format_messages(
        from_lang=from_lang,
        to_lang=to_lang,
        book_details=generate_book_info_prompt(book_title, book_author),
        # source_text=html.escape(text)
        source_text=text
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


def translate_text(
    client: BaseLLM,
    text,
    from_lang,
    to_lang,
    temp_dir=None,
    book_title=None,
    book_author=None,
    chapter_number=None,
):
    """
    Translates HTML text content from one language to another while preserving HTML structure.

    Args:
        client (BaseLLM): The language model client used for translation
        text (str): The HTML text content to translate
        from_lang (str): Source language code
        to_lang (str): Target language code
        temp_dir (str, optional): Directory to save intermediate translation chunks. Defaults to None
        book_title (str, optional): Title of the book being translated. Defaults to None
        book_author (str, optional): Author of the book being translated. Defaults to None
        chapter_number (int, optional): Current chapter number being translated. Defaults to None

    Returns:
        str: The translated HTML text with preserved structure
    """
    translated_chunks = []

    soup = BeautifulSoup(text, 'html.parser')

    if not soup.body:
        return text

    minified_html, mininifed_mapping = minify_attributes(str(soup.body))
    chunks = split_html_by_newline(minified_html)

    for i, chunk in enumerate(chunks):
        print("\tTranslating chunk %d/%d..." % (i+1, len(chunks)))
        translated_chunks.append(translate_chunk(client, chunk, from_lang, to_lang, book_title, book_author))

        save_chunk_to_file(temp_dir, chapter_number, translated_chunks, i)

    translated_restored_html = restore_attributes("".join(translated_chunks), mininifed_mapping)

    soup.body.clear()
    soup.body.extend(BeautifulSoup(translated_restored_html, 'html.parser').body.contents)

    return str(soup)

def translate(client: BaseLLM, input_epub_path, output_epub_path=None, from_chapter=0, to_chapter=9999, from_lang='EN', to_lang='PL', toc=True):
    book = epub.read_epub(input_epub_path)

    full_from_lang = lang_code_to_full_lang(from_lang)
    full_to_lang = lang_code_to_full_lang(to_lang)

    book.set_unique_metadata('DC', 'language', langcodes.standardize_tag(to_lang))

    book_title = get_metadata_title(book)
    book_author = get_metadata_author(book)

    current_chapter = 1
    chapters_count = len([i for i in book.get_items() if i.get_type() == ebooklib.ITEM_DOCUMENT])

    temp_dir = tempfile.mkdtemp()
    print("Debugging: Translated chunks will be stored in the temporary directory: %s" % temp_dir)

    prompt = TRANSLATE_PROMPT.format_messages(
        from_lang=full_from_lang,
        to_lang=full_to_lang,
        book_details=generate_book_info_prompt(book_title, book_author),
        source_text="..."
    )[0].content
    indented_prompt = '\n'.join(['\t' + line for line in prompt.split('\n')])
    print("Prompt sample: \n%s" % indented_prompt)

    if toc:
        book.toc = translate_toc(client, book.toc, from_lang, to_lang)

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            preserve_head_links(item)

            if current_chapter >= from_chapter and current_chapter <= to_chapter:
                print("Processing chapter %d/%d..." % (current_chapter, chapters_count))
                soup = BeautifulSoup(item.content, 'html.parser')
                
                try:
                    translated_text = translate_text(
                        client=client,
                        text=str(soup),
                        from_lang=full_from_lang,
                        to_lang=full_to_lang,
                        temp_dir=temp_dir,
                        chapter_number=current_chapter,
                    )
                    item.content = translated_text.encode('utf-8')
                except Exception as e:
                    print(f"Error translating chapter {current_chapter}: {str(e)}")
                    break
                
            current_chapter += 1

    if not output_epub_path:
        output_epub_path = generate_book_filename(to_lang, MODEL_NAME, TEMPERATURE, book_title, book_author)

    epub.write_epub(output_epub_path, book, {})
    print("Translation completed. Output file: %s" % output_epub_path)

def show_chunks(input_epub_path):
    book = epub.read_epub(input_epub_path)

    model_name_tokenizer = MODEL_NAME
    if model_name_tokenizer not in tiktoken.model.MODEL_TO_ENCODING:
        print(f"Warning: Model {MODEL_NAME} is not supported by tiktoken (supported GPT models)")
        print("\tUsing gpt-4o for token counting - note this is approximate and for informational purposes only")
        model_name_tokenizer = "gpt-4o"
    
    encoding = tiktoken.encoding_for_model(model_name_tokenizer)

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

def extract_glossary_to_file(input_epub_path, from_lang="en"):
    book = epub.read_epub(input_epub_path)
    epub_content = [extract_text_from_html(str(item.content)) for item in book.get_items() if item.get_type() == ebooklib.ITEM_DOCUMENT]
    glossary = extract_glossary(epub_content, from_lang, min_count=5)
    
    # Save glossary to JSON file
    output_filename = os.path.splitext(input_epub_path)[0] + '_glossary.json'
    
    # Convert sets to lists for JSON serialization
    json_glossary = {
        "PERSON": list(glossary["PERSON"]),
        "ORG": list(glossary["ORG"]), 
        "GPE": list(glossary["GPE"]),
        "REPEATED": dict(glossary["REPEATED"])
    }

    print(json_glossary)
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(json_glossary, f, ensure_ascii=False, indent=4)
    
    print(f"\nGlossary saved to: {output_filename}")

@app.command('translate', help="Translate the book.")
def translate_command(
    input: str = typer.Option(..., help="Input file path."),
    output: str = typer.Option(None, help="Output file path. By default it will be generated automatically in the format: <title>_<author>_<model>_t<temperature>_<to_lang>.epub"),
    from_chapter: int = typer.Option(0, help="Starting chapter for translation."),
    to_chapter: int = typer.Option(9999, help="Ending chapter for translation."),
    from_lang: str = typer.Option('EN', help="Source language."),
    to_lang: str = typer.Option('PL', help="Target language."),
    toc: bool = typer.Option(True, is_flag=True, help="Translate the table of contents.")
):
    client = get_model(get_api_key(MODEL_VENDOR), MODEL_VENDOR, MODEL_NAME, TEMPERATURE)
    translate(client, input, output, from_chapter, to_chapter, from_lang, to_lang, toc)

@app.command('show-chapters', help="Show the chapters of the book.")
def show_chapters_command(input: str = typer.Option(..., help="Input file path.")):
    show_chapters(input)

@app.command('show-chunks', help="Show the chunks of the book chapters and estimated prices for each.")
def show_chunks_command(input: str = typer.Option(..., help="Input file path.")):
    show_chunks(input)


@app.command("extract-glossary", help="Extract glossary terms from the book.")
def extract_glossary_command(
    input: str = typer.Option(..., help="Input file path."),
    from_lang: str = typer.Option("en", help="Source language."),
):
    extract_glossary_to_file(input, from_lang)


if __name__ == "__main__":
    app()
