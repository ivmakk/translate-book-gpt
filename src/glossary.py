import spacy
from spacy import load
from collections import Counter, defaultdict

from src.html_utils import extract_text_from_html

nlp = spacy.load("en_core_web_sm")

def extract_named_entities(text, min_count=1):
    """Extracts recurring named entities (characters, locations, etc.)."""
    doc = nlp(text)
    entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "GPE", "ORG"]]
    common_entities = [item for item, count in Counter(entities).items() if count >= min_count]
    return common_entities

def extract_glossary(epub_content, from_lang="en", min_count=2):
    """Extract and organize terms for glossary"""
    # Load appropriate language model
    lang_models = {
        "en": "en_core_web_sm",
        "uk": "uk_core_news_sm",
        # Add other language models as needed
    }
    nlp = load(lang_models.get(from_lang, "en_core_web_sm"))
    
    # Initialize collections for different types of terms
    glossary = {
        "PERSON": set(),      # Names
        "ORG": set(),         # Organizations
        "GPE": set(),         # Geographic locations
        "REPEATED": defaultdict(int)  # Track frequency of terms
    }
    
    # Process each chapter/section
    for text in epub_content:
        clean_text = extract_text_from_html(text)
        doc = nlp(clean_text)
        
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in glossary:
                glossary[ent.label_].add(ent.text)
                glossary["REPEATED"][ent.text] += 1

    filtered_glossary = {
        key: {word for word in value if glossary["REPEATED"][word] >= min_count}
        for key, value in glossary.items()
        if key != "REPEATED"
    }
    filtered_glossary["REPEATED"] = {
        word: count for word, count in glossary["REPEATED"].items()
        if count >= min_count
    }
    
    return filtered_glossary