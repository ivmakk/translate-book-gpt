import pytest
from src.utils import generate_book_filename, sanitize_text


def test_generate_book_filename_with_all_params():
    filename = generate_book_filename(
        to_lang="es",
        model="gpt-4",
        temperature=0.7,
        book_title="The Great Gatsby",
        book_author="F. Scott Fitzgerald"
    )
    assert filename == "f.-scott-fitzgerald.the-great-gatsby.gpt-4.t0.7.es.epub"


def test_generate_book_filename_without_author():
    filename = generate_book_filename(
        to_lang="fr",
        model="gpt-3.5",
        temperature=0.8,
        book_title="Don Quixote"
    )
    assert filename == "don-quixote.gpt-3.5.t0.8.fr.epub"


def test_generate_book_filename_without_title():
    filename = generate_book_filename(
        to_lang="de",
        model="gpt-4",
        temperature=0.9,
        book_author="Miguel de Cervantes"
    )
    assert filename == "miguel-de-cervantes.gpt-4.t0.9.de.epub"


def test_generate_book_filename_without_title_and_author():
    filename = generate_book_filename(
        to_lang="it",
        model="gpt-3.5",
        temperature=0.6
    )
    assert filename == "untitled.gpt-3.5.t0.6.it.epub"


def test_sanitize_with_special_chars():
    filename = sanitize_text("Hello! @World% (2023)")
    assert filename == "Hello---World--(2023)"


def test_sanitize_with_allowed_chars():
    filename = sanitize_text("Hello_World-2023.txt")
    assert filename == "Hello_World-2023.txt"


def test_sanitize_with_spaces():
    filename = sanitize_text("My Book Title")
    assert filename == "My-Book-Title"


def test_sanitize_with_unicode():
    filename = sanitize_text("café.txt")
    assert filename == "cafe.txt"

def test_sanitize_text_with_cyrillic():
    assert sanitize_text("Здраво свет") == "Zdravo-svet"

def test_sanitize_text_with_diacritics():
    assert sanitize_text("café études") == "cafe-etudes"

def test_sanitize_text_with_chinese():
    assert sanitize_text("你好世界") == "Ni-Hao-Shi-Jie-"