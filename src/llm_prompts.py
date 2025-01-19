from langchain_core.prompts import ChatPromptTemplate

TRANSLATE_PROMPT_SYSTEM = \
"""You are a professional book translator and {to_lang} native speaker.
Please translate the text from {from_lang} to {to_lang}.
{book_details}
Keep all special characters and HTML tags as in the source text.
Provide THE ENTIRE TRANSLATION in a single response and do not stop until the full text is translated.
PLEASE RETURN ONLY {to_lang} TRANSLATION."""

TRANSLATE_PROMPT = ChatPromptTemplate([
    ("system", TRANSLATE_PROMPT_SYSTEM),
    ("user", "{source_text}")
])


def generate_book_info_prompt(book_title, book_author):
    """
    Generates additional prompt text for book-specific translation context.

    Args:
        book_title (str): Title of the book being translated
        book_author (str): Author of the book being translated 
        p (str): Existing prompt string to append to

    Returns:
        None - modifies p string in place
    """
    book_details = ""

    if book_title:
        book_details += f"The book title is '{book_title}'. \n"

    if book_author:
        book_details += f"The book author is '{book_author}'. \n"

    if book_title or book_author:
        book_details += "Rely on your knowledge of the author and book to determine the appropriate tone and style for the translation. \n"

    return book_details
