import ebooklib
from bs4 import BeautifulSoup, SoupStrainer


def preserve_head_links(item):
    """
    Preserves links in the head of the document by extracting them and re-adding them to the item.

    This works around an ebooklib issue where links in the document head are lost during epub file saving.
    The function parses the head section, finds all link elements, and explicitly adds them back to the item
    to ensure they persist.

    Args:
        item (EpubItem): The epub item (document) to preserve head links for. Must be of type ITEM_DOCUMENT.

    Returns:
        None
    """
    if item.get_type() != ebooklib.ITEM_DOCUMENT:
        return

    # Parse the head of the document
    soup = BeautifulSoup(item.content, 'html.parser', parse_only=SoupStrainer('head'))
    head = soup.head

    if head:
        for link in head.find_all('link'):
            item.add_link(href=link.get('href'), rel=' '.join(link.get('rel')), type=link.get('type'))


def get_metadata_author(book):
    return book.get_metadata('DC', 'creator')[0][0] if book.get_metadata('DC', 'creator') else None


def get_metadata_title(book):
    return book.get_metadata('DC', 'title')[0][0] if book.get_metadata('DC', 'title') else None