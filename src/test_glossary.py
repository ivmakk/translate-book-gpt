import pytest
from src.glossary import extract_named_entities

def test_extract_named_entities_basic() -> None:
    text = "John Smith works at Microsoft in Seattle. John Smith frequently visits Seattle."
    entities = extract_named_entities(text)
    assert "John Smith" in entities
    assert "Seattle" in entities
    assert "Microsoft" in entities

def test_extract_named_entities_min_count() -> None:
    text = "John Smith works at Microsoft. Jane Doe works at Google."
    entities = extract_named_entities(text, min_count=2)
    assert len(entities) == 0  # No entity appears twice

def test_extract_named_entities_empty() -> None:
    text = "The cat sat on the mat."
    entities = extract_named_entities(text)
    assert entities == []

def test_extract_named_entities_mixed_case() -> None:
    text = "John smith works at MICROSOFT. John Smith visits microsoft."
    entities = extract_named_entities(text)
    assert "John Smith" in entities
    assert any(e.lower() == "microsoft" for e in entities)

def test_extract_named_entities_punctuation() -> None:
    text = "John Smith, who works at Microsoft, lives in Seattle. John Smith loves Seattle!"
    entities = extract_named_entities(text)
    assert "John Smith" in entities
    assert "Seattle" in entities
    assert "Microsoft" in entities