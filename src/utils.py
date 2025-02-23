import os
from typing import List, Set

import langcodes
from unidecode import unidecode


def generate_book_filename(
    to_lang: str,
    model: str,
    temperature: float,
    book_title: str | None = None,
    book_author: str | None = None,
) -> str:
    """
    Generate a standardized filename for an ebook based on its metadata and translation parameters.

    Args:
        to_lang: Target language code for the translation (e.g. 'es', 'fr')
        model: Name of the AI model used for translation (e.g. 'gpt-4')
        temperature: Temperature setting used for the translation
        book_title: Title of the book, if available
        book_author: Author of the book, if available

    Returns:
        str: A sanitized filename in the format:
            "<title>_<author>_<model>_t<temperature>_<to_lang>.epub"
            If title/author are missing, parts are omitted or replaced with "untitled"

    Example:
        >>> generate_book_filename("es", "gpt-4", 0.7, "Don Quixote", "Cervantes")
        'cervantes.don-quixote.gpt-4.t0.7.es.epub'
    """
    parts: List[str] = []

    if book_author:
        parts.append(book_author)
    if book_title:
        parts.append(book_title)

    if not book_author and not book_title:
        parts.append("untitled")

    parts.extend([model, f"t{temperature}", to_lang])

    return sanitize_text(".".join(parts)).lower() + ".epub"

def sanitize_text(filename: str, allowed_chars: Set[str] | None = None) -> str:
    """
    Sanitizes a filename by transliterating non-Latin characters to ASCII and removing disallowed characters.
    Args:
        filename (str): The filename to sanitize.
        allowed_chars (Set[str] | None, optional): Set of allowed characters in the filename. 
            If None, defaults to alphanumeric characters plus dots, underscores and hyphens. 
            Defaults to None.
    Returns:
        str: The sanitized filename containing only allowed characters, with disallowed characters 
            replaced by hyphens.
    Example:
        >>> sanitize_text("héllo wörld.txt")
        'hello-world.txt'
        >>> sanitize_text("test@file.txt")
        'test-file.txt'
    """
    # Transliterate non-Latin characters to ASCII
    latin_filename = unidecode(filename)
    
    if not allowed_chars:
        allowed_chars = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-()[]"
        )

    return "".join(c if c in allowed_chars else "-" for c in latin_filename)


def save_chunk_to_file(dir_path, chapter_number, content, i, prefix='translated_text'):
    if dir_path:
        filename = f'{prefix}_{chapter_number}_{i}.html' if chapter_number else f'{prefix}_{i}.html'

        with open(os.path.join(dir_path, filename), 'w', encoding='utf-8') as f:
            f.write(content)


def lang_code_to_full_lang(from_lang):
    return langcodes.Language.make(from_lang.lower()).display_name()


def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
    """
    Truncates text to specified length and adds ellipsis if needed.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the output string (including ellipsis)
        ellipsis: String to append when text is truncated
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(ellipsis)] + ellipsis