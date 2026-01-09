"""URL collection module for two-phase scraping workflow."""

import logging
from typing import List, Tuple, Set
from .crawler import Crawler
from .fetcher import Fetcher

logger = logging.getLogger(__name__)


class URLCollector:
    """Collects URLs in first phase without fetching full content."""

    def __init__(
        self,
        start_url: str,
        max_pages: int = 100,
        max_depth: int = 3,
        url_pattern: str = None,
        delay: float = 0.5,
    ):
        """
        Initialize the URL collector.

        Args:
            start_url: Starting URL
            max_pages: Maximum pages to collect
            max_depth: Maximum depth
            url_pattern: Optional URL pattern filter
            delay: Delay between requests for URL discovery
        """
        self.crawler = Crawler(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            url_pattern=url_pattern,
        )
        self.fetcher = Fetcher(delay=delay, timeout=15.0)
        self.collected_urls: List[Tuple[str, int]] = []  # (url, depth)

    def collect_all_urls(self) -> List[str]:
        """
        Collect all URLs by crawling and extracting links.
        Only fetches pages to discover links, doesn't extract content.

        Returns:
            List of collected URLs
        """
        logger.info("Phase 1: Collecting URLs...")

        collected_count = 0
        failed_count = 0

        try:
            while len(self.collected_urls) < self.crawler.max_pages:
                # Get next URL to explore
                result = self.crawler.get_next_url()
                if result is None:
                    break

                url, depth = result
                self.collected_urls.append((url, depth))

                # Fetch page to discover links
                response = self.fetcher.fetch(url)
                if response is None:
                    failed_count += 1
                    logger.debug(f"Failed to fetch {url} for link discovery")
                    continue

                # Extract links and add to queue
                self.crawler.add_links(url, response.text, depth)
                collected_count += 1

                if collected_count % 10 == 0:
                    logger.info(
                        f"Collected {collected_count} URLs, "
                        f"queue size: {len(self.crawler.queue)}, "
                        f"failed: {failed_count}"
                    )

        except KeyboardInterrupt:
            logger.info("URL collection interrupted by user")
        finally:
            self.fetcher.close()

        # Extract just URLs from collected list
        urls = [url for url, _ in self.collected_urls]

        logger.info(
            f"Phase 1 complete: Collected {len(urls)} URLs "
            f"(successful: {collected_count}, failed: {failed_count})"
        )

        return urls
