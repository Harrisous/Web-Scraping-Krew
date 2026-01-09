"""HTTP fetching module with throttling and error handling."""

import time
import logging
from typing import Optional
from urllib.parse import urlparse
import httpx

logger = logging.getLogger(__name__)


class Fetcher:
    """Handles HTTP requests with throttling and error handling."""

    def __init__(self, delay: float = 1.0, timeout: float = 10.0, max_retries: int = 3):
        """
        Initialize the fetcher.

        Args:
            delay: Delay between requests in seconds
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.last_request_time = 0.0
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            follow_redirects=True,
        )

    def fetch(self, url: str) -> Optional[httpx.Response]:
        """
        Fetch a URL with throttling and error handling.

        Args:
            url: URL to fetch

        Returns:
            Response object if successful, None otherwise
        """
        # Throttle requests
        self._throttle()

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                logger.debug(f"Successfully fetched {url}")
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    # Server error - retry
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(
                            f"Server error {e.response.status_code} for {url}, "
                            f"retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                else:
                    # Client error (4xx) - don't retry
                    logger.warning(f"Client error {e.response.status_code} for {url}: {e}")
                    return None

            except httpx.TimeoutException:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Timeout for {url}, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Timeout after {self.max_retries} attempts for {url}")
                    return None

            except httpx.RequestError as e:
                logger.error(f"Request error for {url}: {e}")
                return None

        return None

    def _throttle(self) -> None:
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self.last_request_time = time.time()

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
