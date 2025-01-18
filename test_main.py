import unittest

from main import split_html_by_newline
from main import to_locale


class TestSplitHtmlByNewline(unittest.TestCase):
    def test_split_html_by_newline_basic(self):
        html_str = "This is a line.\nThis is another line."
        expected = ["This is a line.\nThis is another line."]
        result = split_html_by_newline(html_str)
        self.assertEqual(result, expected)

    def test_split_html_by_newline_with_max_chunk_size(self):
        html_str = "This is a line.\nThis is another line.\nThis is yet another line."
        expected = ["This is a line.\nThis is another line.", "This is yet another line."]
        result = split_html_by_newline(html_str, max_chunk_size=50)
        self.assertEqual(result, expected)

    def test_split_html_by_newline_large_chunk(self):
        html_str = ("This is a very long line that should be split into multiple chunks.\n" * 10)
        result = split_html_by_newline(html_str, max_chunk_size=100)
        self.assertTrue(len(result) > 1)

    def test_split_html_by_newline_empty_string(self):
        html_str = ""
        expected = []
        result = split_html_by_newline(html_str)
        self.assertEqual(result, expected)

    def test_split_html_by_newline_no_newline(self):
        html_str = "This is a line without a newline"
        expected = ["This is a line without a newline"]
        result = split_html_by_newline(html_str)
        self.assertEqual(result, expected)

    def test_split_html_by_newline_with_html_tags(self):
        html_str = "<p>This is a line.</p>\n<p>This is another line.</p>"
        expected = ["<p>This is a line.</p>", "<p>This is another line.</p>"]
        result = split_html_by_newline(html_str, 10)
        self.assertEqual(result, expected)

class TestToLocale(unittest.TestCase):
    def test_to_locale_default(self):
        self.assertEqual(to_locale(), 'en')

    def test_to_locale_specific_language(self):
        self.assertEqual(to_locale('fr'), 'fr')

    def test_to_locale_with_country_code(self):
        self.assertEqual(to_locale('en-US'), 'en-US')

    def test_to_locale_invalid_code(self):
        with self.assertRaises(ValueError):
            to_locale('invalid-code')

    def test_to_locale_empty_string(self):
        with self.assertRaises(ValueError):
            to_locale('')

if __name__ == '__main__':
    unittest.main()