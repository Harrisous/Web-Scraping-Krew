"""Tests for extractor module."""

import pytest
from src.extractor import Extractor


def test_extract_title_from_tag():
    """Test title extraction from <title> tag."""
    html = "<html><head><title>Test Page Title</title></head><body>Content</body></html>"
    extractor = Extractor()
    result = extractor.extract(html, "http://example.com")
    assert result["title"] == "Test Page Title"


def test_extract_title_from_h1():
    """Test title extraction from <h1> tag when <title> is missing."""
    html = "<html><body><h1>Main Heading</h1><p>Content</p></body></html>"
    extractor = Extractor()
    result = extractor.extract(html, "http://example.com")
    assert result["title"] == "Main Heading"


def test_extract_body_text():
    """Test body text extraction."""
    html = """
    <html>
        <body>
            <main>
                <p>This is the main content.</p>
                <p>More content here.</p>
            </main>
        </body>
    </html>
    """
    extractor = Extractor()
    result = extractor.extract(html, "http://example.com")
    assert "main content" in result["body_text"]
    assert "More content" in result["body_text"]


def test_remove_script_tags():
    """Test that script tags are removed from body text."""
    html = """
    <html>
        <body>
            <main>
                <p>Content</p>
                <script>alert('test');</script>
            </main>
        </body>
    </html>
    """
    extractor = Extractor()
    result = extractor.extract(html, "http://example.com")
    assert "alert" not in result["body_text"]


def test_clean_text_normalizes_whitespace():
    """Test that text cleaning normalizes whitespace."""
    extractor = Extractor()
    dirty_text = "This   has    multiple    spaces"
    clean_text = extractor._clean_text(dirty_text)
    assert "  " not in clean_text


def test_extract_with_nav_footer_removed():
    """Test that nav and footer are removed."""
    html = """
    <html>
        <body>
            <nav>Navigation</nav>
            <main>Main content</main>
            <footer>Footer</footer>
        </body>
    </html>
    """
    extractor = Extractor()
    result = extractor.extract(html, "http://example.com")
    assert "Navigation" not in result["body_text"]
    assert "Footer" not in result["body_text"]
    assert "Main content" in result["body_text"]
