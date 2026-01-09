"""JSONL output writer with idempotency support and timestamped output."""

import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Set, Optional

logger = logging.getLogger(__name__)


class Writer:
    """Handles JSONL output with idempotency checks."""

    def __init__(self, output_path: str = "output.jsonl", resume: bool = False, use_timestamp: bool = False):
        """
        Initialize the writer.

        Args:
            output_path: Path to output JSONL file (default: output.jsonl)
            resume: If True, skip URLs already in output file
            use_timestamp: If True, append timestamp hash to filename
        """
        if use_timestamp:
            self.output_path = self._generate_timestamped_path(output_path)
        else:
            self.output_path = Path(output_path)
        
        self.resume = resume
        self.existing_urls: Set[str] = set()

        # Create output directory if needed
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing URLs if resuming
        if resume and self.output_path.exists():
            self._load_existing_urls()

    def _generate_timestamped_path(self, base_path: str = "output.jsonl") -> Path:
        """
        Generate a timestamped output file path by appending hash to base filename.

        Args:
            base_path: Base path to append timestamp to

        Returns:
            Path object with timestamped filename
        """
        # Get current timestamp
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Create hash of timestamp for uniqueness
        timestamp_hash = hashlib.md5(timestamp_str.encode()).hexdigest()[:8]
        
        # Generate filename by appending hash to base path
        base = Path(base_path)
        if base.is_dir() or base_path.endswith("/"):
            # If it's a directory, create file inside
            directory = base if base.is_dir() else Path(base_path)
            filename = f"output_{timestamp_hash}.jsonl"
            return directory / filename
        else:
            # Append hash to stem (filename without extension)
            stem = base.stem
            suffix = base.suffix if base.suffix else ".jsonl"
            return base.parent / f"{stem}_{timestamp_hash}{suffix}"

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
