"""Content extraction and cleaning module."""

import logging
import re
from typing import Optional, Dict
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class Extractor:
    """Extracts and cleans content from HTML."""

    # Elements to remove
    REMOVE_SELECTORS = [
        "script",
        "style",
        "nav",
        "header",
        "footer",
        "aside",
        ".sidebar",
        ".navigation",
        ".menu",
        ".advertisement",
        ".ads",
        ".social-share",
        ".comments",
        "noscript",
    ]

    def extract(self, html_content: str, url: str) -> Dict[str, Optional[str]]:
        """
        Extract title and body text from HTML.

        Args:
            html_content: HTML content to parse
            url: URL of the page (for fallback title)

        Returns:
            Dictionary with 'title' and 'body_text' keys
        """
        try:
            soup = BeautifulSoup(html_content, "lxml")

            # Extract title
            title = self._extract_title(soup, url)

            # Extract main content
            body_text = self._extract_body_text(soup)

            return {
                "title": title,
                "body_text": body_text,
            }

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return {"title": None, "body_text": None}

    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """
        Extract page title.

        Args:
            soup: BeautifulSoup object
            url: URL for fallback

        Returns:
            Page title or None
        """
        # Try <title> tag
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title:
                return title

        # Try <h1> tag
        h1_tag = soup.find("h1")
        if h1_tag:
            title = h1_tag.get_text(strip=True)
            if title:
                return title

        # Try og:title meta tag
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # Fallback to URL
        logger.warning(f"Could not extract title from {url}, using URL as fallback")
        return url

    def _extract_body_text(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract main body text, removing boilerplate.

        Args:
            soup: BeautifulSoup object

        Returns:
            Cleaned body text or None
        """
        # Remove unwanted elements
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

        # Try to find main content container
        main_content = None

        # Try <main> tag
        main_tag = soup.find("main")
        if main_tag:
            main_content = main_tag
        else:
            # Try <article> tag
            article_tag = soup.find("article")
            if article_tag:
                main_content = article_tag
            else:
                # Try common content class names
                for class_name in ["content", "main-content", "post-content", "article-content", "body"]:
                    content_div = soup.find(class_=re.compile(class_name, re.I))
                    if content_div:
                        main_content = content_div
                        break

        # If no main content found, use body
        if not main_content:
            main_content = soup.find("body")
            if not main_content:
                main_content = soup

        # Extract text
        if main_content:
            text = main_content.get_text(separator=" ", strip=True)
            return self._clean_text(text)

        return None

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines (more than 2 consecutive)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text
