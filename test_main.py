import pytest
from main import split_html_by_newline, system_prompt

def test_split_html_by_newline_basic():
    html_str = "This is a line.\nThis is another line."
    expected = ["This is a line.\nThis is another line."]
    result = split_html_by_newline(html_str)
    assert result == expected

def test_split_html_by_newline_with_max_chunk_size():
    html_str = "This is a line.\nThis is another line.\nThis is yet another line."
    expected = ["This is a line.\nThis is another line.", "This is yet another line."]
    result = split_html_by_newline(html_str, max_chunk_size=50)
    assert result == expected

def test_split_html_by_newline_large_chunk():
    html_str = ("This is a very long line that should be split into multiple chunks.\n" * 10)
    result = split_html_by_newline(html_str, max_chunk_size=100)
    assert len(result) > 1

def test_split_html_by_newline_empty_string():
    html_str = ""
    expected = []
    result = split_html_by_newline(html_str)
    assert result == expected

def test_split_html_by_newline_no_newline():
    html_str = "This is a line without a newline"
    expected = ["This is a line without a newline"]
    result = split_html_by_newline(html_str)
    assert result == expected

def test_split_html_by_newline_with_html_tags():
    html_str = "<p>This is a line.</p>\n<p>This is another line.</p>"
    expected = ["<p>This is a line.</p>", "<p>This is another line.</p>"]
    result = split_html_by_newline(html_str, 10)
    assert result == expected

def test_system_prompt_basic():
    from_lang = 'en'
    to_lang = 'fr'
    expected = ("You are a book translator. Translate the text from English to French. "
                "Keep all special characters and HTML tags as in the source text. Return only French translation.")
    result = system_prompt(from_lang, to_lang)
    assert result == expected

def test_system_prompt_basic():
    from_lang = 'en'
    to_lang = 'uk'
    expected = ("You are a book translator. Translate the text from English to Ukrainian. "
                "Keep all special characters and HTML tags as in the source text. Return only Ukrainian translation.")
    result = system_prompt(from_lang, to_lang)
    assert result == expected

def test_system_prompt_with_country_code():
    from_lang = 'en-US'
    to_lang = 'es-ES'
    expected = ("You are a book translator. Translate the text from American English to European Spanish. "
                "Keep all special characters and HTML tags as in the source text. Return only European Spanish translation.")
    result = system_prompt(from_lang, to_lang)
    assert result == expected
