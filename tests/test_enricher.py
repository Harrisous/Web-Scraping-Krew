"""Tests for enricher module."""

import pytest
from src.enricher import Enricher


def test_word_count():
    """Test word count calculation."""
    enricher = Enricher()
    result = enricher.enrich(
        title="Test Title",
        body_text="This is a test sentence with multiple words.",
        url="http://example.com",
    )
    assert result["word_count"] > 0
    assert result["word_count"] == len("Test Title This is a test sentence with multiple words.".split())


def test_char_count():
    """Test character count calculation."""
    enricher = Enricher()
    text = "Test content"
    result = enricher.enrich(
        title="Title",
        body_text=text,
        url="http://example.com",
    )
    assert result["char_count"] > 0
    assert result["char_count"] >= len(text)


def test_language_detection():
    """Test language detection."""
    enricher = Enricher()
    result = enricher.enrich(
        title="Hello World",
        body_text="This is an English text for testing language detection.",
        url="http://example.com",
    )
    assert result["language"] in ["en", "unknown"]


def test_content_type_classification():
    """Test content type classification."""
    enricher = Enricher()
    
    # Product page
    result = enricher.enrich(
        title="Book Title",
        body_text="Book description",
        url="http://example.com/books/book1",
    )
    assert result["content_type"] == "product_page"
    
    # Doc page
    result = enricher.enrich(
        title="Documentation",
        body_text="Docs content",
        url="http://example.com/docs/page",
    )
    assert result["content_type"] == "doc_page"
    
    # Article
    result = enricher.enrich(
        title="Article",
        body_text="Article content " * 20,  # Make it substantial
        url="http://example.com/blog/post",
    )
    assert result["content_type"] == "article"


def test_reading_time_calculation():
    """Test reading time calculation."""
    enricher = Enricher()
    # Create text with known word count
    words = "word " * 200  # 200 words
    result = enricher.enrich(
        title="Title",
        body_text=words,
        url="http://example.com",
    )
    # Should be approximately 1 minute (200 words / 200 WPM)
    assert 0.9 <= result["reading_time_minutes"] <= 1.1


def test_has_code_detection():
    """Test code detection."""
    enricher = Enricher()
    
    # Text with code
    result = enricher.enrich(
        title="Code Example",
        body_text="def function_name(): return True",
        url="http://example.com",
    )
    assert result["has_code"] is True
    
    # Text without code
    result = enricher.enrich(
        title="Regular Text",
        body_text="This is just regular text without any code.",
        url="http://example.com",
    )
    assert result["has_code"] is False


def test_fetched_at_timestamp():
    """Test that fetched_at timestamp is included."""
    enricher = Enricher()
    result = enricher.enrich(
        title="Test",
        body_text="Content",
        url="http://example.com",
    )
    assert "fetched_at" in result
    assert result["fetched_at"].endswith("Z")  # UTC timestamp
