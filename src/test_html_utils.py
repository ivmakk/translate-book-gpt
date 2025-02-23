import pytest
from src.html_utils import format_html_to_multiline_block_tags, minify_attributes, restore_attributes

def test_minify_single_attribute():
    html = '<div class="my-class">Content</div>'
    expected_minified = '<div class="v1">Content</div>'
    expected_mapping = {'v1': 'my-class'}
    
    minified, mapping = minify_attributes(html)
    
    assert minified == expected_minified
    assert mapping == expected_mapping

def test_minify_multiple_attributes():
    html = '<div class="my-class" id="my-id">Content</div>'
    expected_minified = '<div class="v1" id="v2">Content</div>'
    expected_mapping = {'v1': 'my-class', 'v2': 'my-id'}
    
    minified, mapping = minify_attributes(html)
    
    assert minified == expected_minified
    assert mapping == expected_mapping

def test_minify_repeated_attributes():
    html = '<div class="my-class" id="my-id">Content</div><span class="my-class">More Content</span>'
    expected_minified = '<div class="v1" id="v2">Content</div><span class="v1">More Content</span>'
    expected_mapping = {'v1': 'my-class', 'v2': 'my-id'}
    
    minified, mapping = minify_attributes(html)
    
    assert minified == expected_minified
    assert mapping == expected_mapping

def test_minify_no_attributes():
    html = '<div>Content</div>'
    expected_minified = '<div>Content</div>'
    expected_mapping = {}
    
    minified, mapping = minify_attributes(html)
    
    assert minified == expected_minified
    assert mapping == expected_mapping

def test_restore_single_attribute():
    minified_html = '<div class="v1">Content</div>'
    attribute_mapping = {'v1': 'my-class'}
    expected_html = '<div class="my-class">Content</div>'
    
    restored_html = restore_attributes(minified_html, attribute_mapping)
    
    assert restored_html == expected_html

def test_restore_multiple_attributes():
    minified_html = '<div class="v1" id="v2">Content</div>'
    attribute_mapping = {'v1': 'my-class', 'v2': 'my-id'}
    expected_html = '<div class="my-class" id="my-id">Content</div>'
    
    restored_html = restore_attributes(minified_html, attribute_mapping)
    
    assert restored_html == expected_html

def test_restore_repeated_attributes():
    minified_html = '<div class="v1" id="v2">Content</div><span class="v1">More Content</span>'
    attribute_mapping = {'v1': 'my-class', 'v2': 'my-id'}
    expected_html = '<div class="my-class" id="my-id">Content</div><span class="my-class">More Content</span>'
    
    restored_html = restore_attributes(minified_html, attribute_mapping)
    
    assert restored_html == expected_html

def test_restore_no_attributes():
    minified_html = '<div>Content</div>'
    attribute_mapping = {}
    expected_html = '<div>Content</div>'
    
    restored_html = restore_attributes(minified_html, attribute_mapping)
    
    assert restored_html == expected_html

def test_restore_with_data_attributes():
    minified_html = '<div data-name="v1" data-value="v2">Content</div>'
    attribute_mapping = {'v1': 'my-data', 'v2': '123'}
    expected_html = '<div data-name="my-data" data-value="123">Content</div>'
    
    restored_html = restore_attributes(minified_html, attribute_mapping)
    
    assert restored_html == expected_html

def test_format_html_to_multiline_block_tags():
    html = '<span class="p1"><p>Title</p><p>First paragraph.</p><p>Second paragraph.</p>'
    expected = '<span class="p1"><p>Title</p>\n<p>First paragraph.</p>\n<p>Second paragraph.</p>\n'
    
    result = format_html_to_multiline_block_tags(html)
    
    assert result == expected

def test_format_html_to_multiline_block_tags_empty():
    html = ""
    expected = ""
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_single_paragraph():
    html = "<p>Test paragraph</p>"
    expected = "<p>Test paragraph</p>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_multiple():
    html = "<p>First</p><p>Second</p><p>Third</p>"
    expected = "<p>First</p>\n<p>Second</p>\n<p>Third</p>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_existing_newlines():
    html = "<p>First</p>\n<p>Second</p>\n<p>Third</p>"
    expected = "<p>First</p>\n<p>Second</p>\n<p>Third</p>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_mixed_tags() -> None:
    html = "<div>Container<p>Paragraph</p><h1>Heading</h1></div>"
    expected = "<div>Container<p>Paragraph</p>\n<h1>Heading</h1>\n</div>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_nested_tags() -> None:
    html = "<div><p>Outer<div>Inner</div>End</p></div>"
    expected = "<div><p>Outer<div>Inner</div>\nEnd</p>\n</div>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_all_heading_levels() -> None:
    html = "<h1>H1</h1><h2>H2</h2><h3>H3</h3><h4>H4</h4><h5>H5</h5><h6>H6</h6>"
    expected = "<h1>H1</h1>\n<h2>H2</h2>\n<h3>H3</h3>\n<h4>H4</h4>\n<h5>H5</h5>\n<h6>H6</h6>\n"
    assert format_html_to_multiline_block_tags(html) == expected

def test_format_html_to_multiline_block_tags_with_content() -> None:
    html = "<div>Text<p>More text</p>Final</div>"
    expected = "<div>Text<p>More text</p>\nFinal</div>\n"
    assert format_html_to_multiline_block_tags(html) == expected

