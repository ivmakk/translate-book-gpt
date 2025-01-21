from bs4 import BeautifulSoup

from main import MAX_CHUNK_SIZE

def minify_attributes(html: str):
    """
    Minifies HTML attributes by replacing their values with shorter placeholders.
    
    Args:
        html (str): The HTML content to minify
        
    Returns:
        tuple: A tuple containing:
            - str: The minified HTML with placeholder attribute values
            - dict: Mapping of placeholders to original attribute values
            
    Example:
        html = '<div class="my-class" id="my-id">Content</div>'
        minified, mapping = minify_attributes(html)
        # minified = '<div class="v1" id="v2">Content</div>'
        # mapping = {'v1': 'my-class', 'v2': 'my-id'}
    """
    attributes_to_minify = ['id', 'class', 'src', 'alt', 'href', 'title']

    soup = BeautifulSoup(html, 'html.parser')
    attribute_mapping = {}
    value_to_placeholder = {}  # Keep track of already mapped values
    placeholder_counter = 1

    for tag in soup.find_all():
        for attr in sorted(attributes_to_minify):
            if attr in tag.attrs:
                original_value = tag[attr]
                
                # Convert list-type attributes (like classes) to space-separated string
                if isinstance(original_value, list):
                    original_value = ' '.join(original_value)
                
                # If we've seen this value before, use the existing placeholder
                if original_value in value_to_placeholder:
                    placeholder = value_to_placeholder[original_value]
                else:
                    # Create new placeholder for new values
                    placeholder = f"v{placeholder_counter}"
                    value_to_placeholder[original_value] = placeholder
                    attribute_mapping[placeholder] = original_value
                    placeholder_counter += 1
                
                tag[attr] = placeholder

    return str(soup), attribute_mapping


def restore_attributes(minified_html: str, attribute_mapping: dict) -> str:
    """
    Restores original attribute values from a minified HTML string using the provided mapping.
    
    Args:
        minified_html (str): The minified HTML with placeholder attribute values
        attribute_mapping (dict): Mapping of placeholders to original attribute values
        
    Returns:
        str: The HTML with original attribute values restored
        
    Example:
        minified = '<div class="v1" id="v2">Content</div>'
        mapping = {'v1': 'my-class', 'v2': 'my-id'}
        restored = restore_attributes(minified, mapping)
        # restored = '<div class="my-class" id="my-id">Content</div>'
    """
    soup = BeautifulSoup(minified_html, 'html.parser')
    for tag in soup.find_all():
        for attr, value in tag.attrs.items():
            # Convert list-type attributes to space-separated string
            if isinstance(value, list):
                value = ' '.join(value)
                
            if value in attribute_mapping:
                tag[attr] = attribute_mapping[value]
    return str(soup)


def split_html_by_sentence(html_str, max_chunk_size=MAX_CHUNK_SIZE):
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


def split_html_by_newline(html_str, max_chunk_size=MAX_CHUNK_SIZE):
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