"""Async HTTP fetching module with concurrent requests."""

import asyncio
import logging
from typing import Optional, List, Tuple
import httpx

logger = logging.getLogger(__name__)


class AsyncFetcher:
    """Handles async HTTP requests with concurrency control."""

    def __init__(
        self,
        max_concurrent: int = 10,
        timeout: float = 30.0,
        max_retries: int = 3,
        delay: float = 0.1,
    ):
        """
        Initialize the async fetcher.

        Args:
            max_concurrent: Maximum concurrent requests
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            delay: Minimum delay between requests (for rate limiting)
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.aclose()

    async def fetch(self, url: str) -> Tuple[str, Optional[httpx.Response]]:
        """
        Fetch a URL with concurrency control and error handling.

        Args:
            url: URL to fetch

        Returns:
            Tuple of (url, response) where response is None on failure
        """
        async with self.semaphore:
            # Rate limiting delay
            await asyncio.sleep(self.delay)

            # Retry logic
            for attempt in range(self.max_retries):
                try:
                    response = await self.client.get(url)
                    response.raise_for_status()
                    logger.debug(f"Successfully fetched {url}")
                    return (url, response)

                except httpx.HTTPStatusError as e:
                    if e.response.status_code >= 500:
                        # Server error - retry
                        if attempt < self.max_retries - 1:
                            wait_time = 2 ** attempt
                            logger.debug(
                                f"Server error {e.response.status_code} for {url}, "
                                f"retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                    else:
                        # Client error (4xx) - don't retry
                        logger.debug(f"Client error {e.response.status_code} for {url}")
                        return (url, None)

                except httpx.TimeoutException:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.debug(
                            f"Timeout for {url}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.debug(f"Timeout after {self.max_retries} attempts for {url}")
                        return (url, None)

                except httpx.RequestError as e:
                    logger.debug(f"Request error for {url}: {e}")
                    return (url, None)

            return (url, None)

    async def fetch_batch(
        self, urls: List[str]
    ) -> List[Tuple[str, Optional[httpx.Response]]]:
        """
        Fetch multiple URLs concurrently.

        Args:
            urls: List of URLs to fetch

        Returns:
            List of tuples (url, response)
        """
        tasks = [self.fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
        return results
