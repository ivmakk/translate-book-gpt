import pytest
from src.html_utils import minify_attributes, restore_attributes

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