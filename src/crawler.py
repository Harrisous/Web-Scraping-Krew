"""URL crawling module with link extraction and filtering."""

import logging
import re
from typing import Set, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque

logger = logging.getLogger(__name__)


class Crawler:
    """Manages URL crawling with deduplication and filtering."""

    # Patterns to skip
    SKIP_PATTERNS = [
        r"/login",
        r"/signin",
        r"/signup",
        r"/register",
        r"/search\?",
        r"/cart",
        r"/checkout",
        r"\.(pdf|jpg|jpeg|png|gif|svg|css|js|zip|tar|gz)$",
        r"#",
        r"mailto:",
        r"tel:",
    ]

    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 3,
        url_pattern: Optional[str] = None,
    ):
        """
        Initialize the crawler.

        Args:
            start_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum depth to crawl
            url_pattern: Optional regex pattern to filter URLs
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.url_pattern = url_pattern

        # Parse base domain
        parsed = urlparse(start_url)
        self.base_domain = f"{parsed.scheme}://{parsed.netloc}"
        self.base_path = parsed.path.rstrip("/")

        # Tracking
        self.visited: Set[str] = set()
        self.url_depths: dict[str, int] = {}  # Track depth for each URL
        self.queue: deque = deque([(start_url, 0)])  # (url, depth)
        self.scraped_count = 0

    def get_next_url(self) -> Optional[Tuple[str, int]]:
        """
        Get the next URL to scrape with its depth.

        Returns:
            Tuple of (url, depth) or None if queue is empty or limit reached
        """
        if self.scraped_count >= self.max_pages:
            return None

        if not self.queue:
            return None

        url, depth = self.queue.popleft()

        # Normalize URL
        url = self._normalize_url(url)

        # Check if already visited
        if url in self.visited:
            return self.get_next_url()

        # Check depth limit
        if depth > self.max_depth:
            return self.get_next_url()

        # Check if should skip
        if self._should_skip(url):
            return self.get_next_url()

        self.visited.add(url)
        self.url_depths[url] = depth
        self.scraped_count += 1
        return (url, depth)

    def add_links(self, base_url: str, html_content: str, current_depth: int) -> None:
        """
        Extract and add links from HTML content.

        Args:
            base_url: Base URL for resolving relative links
            html_content: HTML content to parse
            current_depth: Current crawling depth
        """
        from bs4 import BeautifulSoup

        try:
            soup = BeautifulSoup(html_content, "lxml")
            links = soup.find_all("a", href=True)

            for link in links:
                href = link.get("href", "").strip()
                if not href:
                    continue

                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                normalized_url = self._normalize_url(absolute_url)

                # Check if same domain
                if not self._is_same_domain(normalized_url):
                    continue

                # Check if already visited or in queue
                if normalized_url in self.visited:
                    continue

                # Check if should skip
                if self._should_skip(normalized_url):
                    continue

                # Check URL pattern filter
                if self.url_pattern and not re.search(self.url_pattern, normalized_url):
                    continue

                # Check if already in queue
                if any(url == normalized_url for url, _ in self.queue):
                    continue

                # Add to queue
                self.queue.append((normalized_url, current_depth + 1))
                logger.debug(f"Added to queue: {normalized_url} (depth {current_depth + 1})")

        except Exception as e:
            logger.warning(f"Error extracting links from {base_url}: {e}")

    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by removing fragments and trailing slashes.

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        parsed = urlparse(url)
        # Remove fragment
        normalized = urlunparse(
            (parsed.scheme, parsed.netloc, parsed.path, parsed.params, parsed.query, "")
        )
        # Remove trailing slash (except for root)
        if normalized.endswith("/") and len(parsed.path) > 1:
            normalized = normalized.rstrip("/")
        return normalized

    def _is_same_domain(self, url: str) -> bool:
        """
        Check if URL is from the same domain.

        Args:
            url: URL to check

        Returns:
            True if same domain, False otherwise
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc == urlparse(self.start_url).netloc
        except Exception:
            return False

    def _should_skip(self, url: str) -> bool:
        """
        Check if URL should be skipped based on patterns.

        Args:
            url: URL to check

        Returns:
            True if should skip, False otherwise
        """
        url_lower = url.lower()
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, url_lower, re.IGNORECASE):
                return True
        return False

    def get_current_depth(self, url: str) -> int:
        """
        Get the depth of a URL in the crawl tree.

        Args:
            url: URL to check

        Returns:
            Depth of the URL
        """
        url = self._normalize_url(url)
        return self.url_depths.get(url, 0)
