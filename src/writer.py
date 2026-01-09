"""JSONL output writer with idempotency support."""

import json
import logging
from pathlib import Path
from typing import Set, Optional

logger = logging.getLogger(__name__)


class Writer:
    """Handles JSONL output with idempotency checks."""

    def __init__(self, output_path: str, resume: bool = False):
        """
        Initialize the writer.

        Args:
            output_path: Path to output JSONL file
            resume: If True, skip URLs already in output file
        """
        self.output_path = Path(output_path)
        self.resume = resume
        self.existing_urls: Set[str] = set()

        # Create output directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing URLs if resuming
        if resume and self.output_path.exists():
            self._load_existing_urls()

    def _load_existing_urls(self) -> None:
        """Load URLs from existing output file for idempotency."""
        try:
            with open(self.output_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        doc = json.loads(line)
                        if "url" in doc:
                            self.existing_urls.add(doc["url"])
                    except json.JSONDecodeError:
                        logger.warning(f"Could not parse line in {self.output_path}")
            logger.info(f"Loaded {len(self.existing_urls)} existing URLs for resume mode")
        except Exception as e:
            logger.warning(f"Error loading existing URLs: {e}")

    def should_skip(self, url: str) -> bool:
        """
        Check if URL should be skipped (already processed).

        Args:
            url: URL to check

        Returns:
            True if should skip, False otherwise
        """
        if not self.resume:
            return False
        return url in self.existing_urls

    def write(self, document: dict) -> bool:
        """
        Write document to JSONL file.

        Args:
            document: Document dictionary to write

        Returns:
            True if written successfully, False otherwise
        """
        try:
            # Validate required fields
            if "url" not in document:
                logger.error("Document missing 'url' field")
                return False

            # Check if should skip
            if self.should_skip(document["url"]):
                logger.debug(f"Skipping already processed URL: {document['url']}")
                return False

            # Write to file (append mode)
            with open(self.output_path, "a", encoding="utf-8") as f:
                json_line = json.dumps(document, ensure_ascii=False)
                f.write(json_line + "\n")

            # Track written URL
            if self.resume:
                self.existing_urls.add(document["url"])

            return True

        except Exception as e:
            logger.error(f"Error writing document: {e}")
            return False

    def get_written_count(self) -> int:
        """
        Get count of documents written.

        Returns:
            Number of documents written
        """
        if not self.output_path.exists():
            return 0

        try:
            count = 0
            with open(self.output_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except Exception:
            return 0
