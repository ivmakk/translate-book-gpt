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
    assert filename == "the-great-gatsby_f.-scott-fitzgerald_gpt-4_t0.7_es.epub"


def test_generate_book_filename_without_author():
    filename = generate_book_filename(
        to_lang="fr",
        model="gpt-3.5",
        temperature=0.8,
        book_title="Don Quixote"
    )
    assert filename == "don-quixote_gpt-3.5_t0.8_fr.epub"


def test_generate_book_filename_without_title():
    filename = generate_book_filename(
        to_lang="de",
        model="gpt-4",
        temperature=0.9,
        book_author="Miguel de Cervantes"
    )
    assert filename == "miguel-de-cervantes_gpt-4_t0.9_de.epub"


def test_generate_book_filename_without_title_and_author():
    filename = generate_book_filename(
        to_lang="it",
        model="gpt-3.5",
        temperature=0.6
    )
    assert filename == "untitled_gpt-3.5_t0.6_it.epub"


def test_sanitize_filename_with_special_chars():
    filename = sanitize_text("Hello! @World% (2023)")
    assert filename == "Hello---World---2023-"


def test_sanitize_filename_with_allowed_chars():
    filename = sanitize_text("Hello_World-2023.txt")
    assert filename == "Hello_World-2023.txt"


def test_sanitize_filename_with_spaces():
    filename = sanitize_text("My Book Title")
    assert filename == "My-Book-Title"


def test_sanitize_filename_with_unicode():
    filename = sanitize_text("café.txt")
    assert filename == "caf-.txt" 