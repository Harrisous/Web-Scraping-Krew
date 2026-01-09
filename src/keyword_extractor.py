"""Keyword extraction module for AI workflows."""

import logging
import re
from typing import List, Optional
import nltk
from rake_nltk import Rake

logger = logging.getLogger(__name__)

# Download required NLTK data if not already present
def _ensure_nltk_data():
    """Ensure required NLTK data is downloaded."""
    # Try to find punkt_tab (newer NLTK versions) first
    punkt_found = False
    try:
        nltk.data.find('tokenizers/punkt_tab')
        punkt_found = True
    except LookupError:
        try:
            nltk.data.find('tokenizers/punkt')
            punkt_found = True
        except LookupError:
            pass
    
    if not punkt_found:
        logger.info("Downloading NLTK punkt tokenizer (punkt_tab)...")
        try:
            # Try newer punkt_tab first (required by newer rake-nltk)
            # Use quiet=True but verify download completed
            nltk.download('punkt_tab', quiet=True)
            # Verify it was downloaded successfully
            nltk.data.find('tokenizers/punkt_tab')
            logger.debug("punkt_tab downloaded successfully")
        except Exception as e1:
            logger.info(f"punkt_tab download failed, trying punkt: {e1}")
            try:
                # Fallback to older punkt
                nltk.download('punkt', quiet=True)
                nltk.data.find('tokenizers/punkt')
                logger.debug("punkt downloaded successfully")
            except Exception as e2:
                logger.warning(f"Could not download NLTK punkt tokenizer: {e2}")

    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        logger.info("Downloading NLTK stopwords...")
        try:
            nltk.download('stopwords', quiet=True)
        except Exception as e:
            logger.warning(f"Could not download NLTK stopwords: {e}")

# Download data on module import
_ensure_nltk_data()


class KeywordExtractor:
    """Extracts keywords from text content for AI workflows."""

    def __init__(self, max_keywords: int = 10):
        """
        Initialize the keyword extractor.

        Args:
            max_keywords: Maximum number of keywords to extract
        """
        # Ensure NLTK data is available before initializing Rake
        _ensure_nltk_data()
        
        self.max_keywords = max_keywords
        
        # Initialize Rake with error handling
        try:
            self.rake = Rake(
                min_length=2,  # Minimum word length
                max_length=3,  # Maximum phrase length
                include_repeated_phrases=False,
            )
        except LookupError as e:
            # If punkt_tab is still missing, try downloading it again
            if 'punkt_tab' in str(e) or 'punkt' in str(e):
                logger.info("punkt_tab not found, attempting download...")
                try:
                    nltk.download('punkt_tab', quiet=True)
                    # Verify download and retry initialization
                    nltk.data.find('tokenizers/punkt_tab')
                    self.rake = Rake(
                        min_length=2,
                        max_length=3,
                        include_repeated_phrases=False,
                    )
                    logger.debug("Rake initialized successfully after punkt_tab download")
                except Exception as download_error:
                    logger.warning(f"Could not initialize Rake with punkt_tab: {download_error}")
                    logger.warning("Will use fallback keyword extraction")
                    self.rake = None
            else:
                raise

    def extract(self, title: Optional[str], body_text: Optional[str]) -> List[str]:
        """
        Extract keywords from title and body text.

        Args:
            title: Document title
            body_text: Document body text

        Returns:
            List of extracted keywords
        """
        if not body_text and not title:
            return []

        # Combine title and body for keyword extraction
        text = ""
        if title:
            text += title + " "
        if body_text:
            text += body_text

        if not text or len(text.strip()) < 10:
            return []

        # If Rake initialization failed, use fallback immediately
        if self.rake is None:
            return self._fallback_keyword_extraction(text)

        try:
            # Extract keywords using RAKE
            self.rake.extract_keywords_from_text(text)
            keywords = self.rake.get_ranked_phrases()[:self.max_keywords]

            # Clean and normalize keywords
            cleaned_keywords = []
            for keyword in keywords:
                cleaned = self._clean_keyword(keyword)
                if cleaned and len(cleaned) > 2:  # Minimum keyword length
                    cleaned_keywords.append(cleaned)

            return cleaned_keywords[:self.max_keywords]

        except Exception as e:
            logger.warning(f"Error extracting keywords: {e}")
            # Fallback: extract simple words
            return self._fallback_keyword_extraction(text)

    def _clean_keyword(self, keyword: str) -> str:
        """
        Clean and normalize a keyword.

        Args:
            keyword: Raw keyword phrase

        Returns:
            Cleaned keyword
        """
        # Remove extra whitespace
        keyword = re.sub(r"\s+", " ", keyword.strip())

        # Remove special characters except spaces and hyphens
        keyword = re.sub(r"[^\w\s-]", "", keyword)

        # Convert to lowercase
        keyword = keyword.lower()

        # Remove very short words
        words = keyword.split()
        filtered_words = [w for w in words if len(w) > 2]
        
        return " ".join(filtered_words) if filtered_words else ""

    def _fallback_keyword_extraction(self, text: str) -> List[str]:
        """
        Fallback keyword extraction using simple word frequency.

        Args:
            text: Text to extract keywords from

        Returns:
            List of keywords
        """
        # Remove common stop words and short words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "have", "has", "had", "do", "does", "did", "will", "would",
            "could", "should", "may", "might", "must", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they",
            "what", "which", "who", "when", "where", "why", "how", "all",
            "each", "every", "some", "any", "no", "not", "more", "most",
        }

        # Extract words
        words = re.findall(r"\b[a-z]{3,}\b", text.lower())
        
        # Count frequency
        word_freq = {}
        for word in words:
            if word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, _ in sorted_words[:self.max_keywords]]

        return keywords
