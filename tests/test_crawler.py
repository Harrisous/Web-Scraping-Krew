"""Tests for crawler module."""

import pytest
from src.crawler import Crawler


def test_crawler_initialization():
    """Test crawler initialization."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
    )
    assert crawler.start_url == "http://example.com"
    assert crawler.max_pages == 10
    assert crawler.max_depth == 2


def test_get_next_url():
    """Test getting next URL from queue."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=5,
        max_depth=2,
    )
    result = crawler.get_next_url()
    assert result is not None
    url, depth = result
    assert url == "http://example.com"
    assert depth == 0
    assert url in crawler.visited


def test_url_normalization():
    """Test URL normalization."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
    )
    # Remove trailing slash
    normalized = crawler._normalize_url("http://example.com/page/")
    assert normalized == "http://example.com/page"
    
    # Remove fragment
    normalized = crawler._normalize_url("http://example.com/page#section")
    assert normalized == "http://example.com/page"


def test_same_domain_check():
    """Test same domain checking."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
    )
    assert crawler._is_same_domain("http://example.com/page") is True
    assert crawler._is_same_domain("http://other.com/page") is False


def test_skip_patterns():
    """Test URL skip patterns."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
    )
    assert crawler._should_skip("http://example.com/login") is True
    assert crawler._should_skip("http://example.com/search?q=test") is True
    assert crawler._should_skip("http://example.com/page.pdf") is True
    assert crawler._should_skip("http://example.com/normal-page") is False


def test_add_links():
    """Test adding links from HTML."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
    )
    
    html = """
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="/page2">Page 2</a>
            <a href="http://external.com">External</a>
        </body>
    </html>
    """
    
    crawler.add_links("http://example.com", html, current_depth=0)
    
    # Should have added internal links to queue
    assert len(crawler.queue) > 0
    
    # Get next URL should return start URL
    result = crawler.get_next_url()
    assert result is not None
    url, depth = result
    assert url == "http://example.com"
    assert depth == 0


def test_url_pattern_filtering():
    """Test URL pattern filtering."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=10,
        max_depth=2,
        url_pattern=r"/books/",
    )
    
    html = """
    <html>
        <body>
            <a href="/books/book1">Book 1</a>
            <a href="/articles/article1">Article 1</a>
        </body>
    </html>
    """
    
    crawler.add_links("http://example.com", html, current_depth=0)
    
    # Only /books/ URLs should be in queue
    urls_in_queue = [url for url, _ in crawler.queue]
    assert any("/books/" in url for url in urls_in_queue)
    assert not any("/articles/" in url for url in urls_in_queue)


def test_max_pages_limit():
    """Test that max_pages limit is respected."""
    crawler = Crawler(
        start_url="http://example.com",
        max_pages=3,
        max_depth=2,
    )
    
    # Get URLs up to max_pages
    urls = []
    for _ in range(5):  # Try to get more than max
        url = crawler.get_next_url()
        if url is None:
            break
        urls.append(url)
    
    assert len(urls) <= 3
