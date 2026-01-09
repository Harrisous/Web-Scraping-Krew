"""AI collections enrichment module."""

import logging
import re
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlparse
import langdetect
from langdetect import LangDetectException

logger = logging.getLogger(__name__)


class Enricher:
    """Enriches documents with metadata for AI workflows."""

    # Average reading speed (words per minute)
    WORDS_PER_MINUTE = 200

    def enrich(self, title: Optional[str], body_text: Optional[str], url: str) -> Dict:
        """
        Enrich document with metadata.

        Args:
            title: Document title
            body_text: Document body text
            url: Document URL

        Returns:
            Enriched document dictionary
        """
        # Combine title and body for analysis
        full_text = ""
        if title:
            full_text += title + " "
        if body_text:
            full_text += body_text

        # Word and character counts
        word_count = len(full_text.split()) if full_text else 0
        char_count = len(full_text) if full_text else 0

        # Language detection
        language = self._detect_language(full_text)

        # Content type classification
        content_type = self._classify_content_type(url, title, body_text)

        # Reading time
        reading_time_minutes = word_count / self.WORDS_PER_MINUTE if word_count > 0 else 0.0

        # Additional signals
        has_code = self._has_code_blocks(body_text) if body_text else False
        has_images = False  # Could be enhanced by checking HTML

        return {
            "word_count": word_count,
            "char_count": char_count,
            "language": language,
            "content_type": content_type,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "reading_time_minutes": round(reading_time_minutes, 2),
            "has_code": has_code,
            "has_images": has_images,
        }

    def _detect_language(self, text: str) -> str:
        """
        Detect language of text.

        Args:
            text: Text to analyze

        Returns:
            ISO 639-1 language code or 'unknown'
        """
        if not text or len(text.strip()) < 10:
            return "unknown"

        try:
            detected = langdetect.detect(text)
            return detected
        except LangDetectException:
            logger.warning("Could not detect language")
            return "unknown"

    def _classify_content_type(self, url: str, title: Optional[str], body_text: Optional[str]) -> str:
        """
        Classify content type based on URL and content.

        Args:
            url: Document URL
            title: Document title
            body_text: Document body text

        Returns:
            Content type classification
        """
        url_lower = url.lower()
        path = urlparse(url).path.lower()

        # Product/page classification (for books.toscrape.com)
        if "/books/" in path or "/book/" in path or "/product/" in path:
            return "product_page"

        # Documentation
        if "/docs/" in path or "/documentation/" in path or "/guide/" in path:
            return "doc_page"

        # Blog/article
        if "/blog/" in path or "/article/" in path or "/post/" in path or "/news/" in path:
            return "article"

        # Homepage
        if path == "/" or path == "":
            return "homepage"

        # Category/listing page
        if "/category/" in path or "/tag/" in path or "/archive/" in path:
            return "listing_page"

        # Default to article if has substantial content
        if body_text and len(body_text.split()) > 100:
            return "article"

        return "other"

    def _has_code_blocks(self, text: Optional[str]) -> bool:
        """
        Check if text contains code-like patterns.

        Args:
            text: Text to check

        Returns:
            True if likely contains code
        """
        if not text:
            return False

        # Simple heuristics for code detection
        code_indicators = [
            r"def\s+\w+\s*\(",
            r"function\s+\w+\s*\(",
            r"class\s+\w+",
            r"import\s+\w+",
            r"from\s+\w+\s+import",
            r"<\?php",
            r"console\.log",
            r"public\s+static",
        ]

        for pattern in code_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False
