import pytest
from src.html_utils import split_html_by_newline

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
