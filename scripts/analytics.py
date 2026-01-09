"""Analytics script to analyze scraped data."""

import json
import sys
from pathlib import Path
from collections import Counter
from typing import Dict, List


def load_jsonl(file_path: str) -> List[Dict]:
    """
    Load documents from JSONL file.

    Args:
        file_path: Path to JSONL file

    Returns:
        List of document dictionaries
    """
    documents = []
    path = Path(file_path)

    if not path.exists():
        print(f"Error: File {file_path} does not exist")
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                documents.append(doc)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line {line_num}: {e}")

    return documents


def calculate_statistics(documents: List[Dict]) -> Dict:
    """
    Calculate statistics from documents.

    Args:
        documents: List of document dictionaries

    Returns:
        Dictionary of statistics
    """
    if not documents:
        return {}

    # Basic counts
    total_docs = len(documents)

    # Word and character counts
    word_counts = [doc.get("word_count", 0) for doc in documents]
    char_counts = [doc.get("char_count", 0) for doc in documents]

    avg_word_count = sum(word_counts) / total_docs if word_counts else 0
    avg_char_count = sum(char_counts) / total_docs if char_counts else 0
    min_word_count = min(word_counts) if word_counts else 0
    max_word_count = max(word_counts) if word_counts else 0

    # Language distribution
    languages = [doc.get("language", "unknown") for doc in documents]
    language_dist = Counter(languages)

    # Content type distribution
    content_types = [doc.get("content_type", "unknown") for doc in documents]
    content_type_dist = Counter(content_types)

    # Reading time
    reading_times = [doc.get("reading_time_minutes", 0) for doc in documents]
    avg_reading_time = sum(reading_times) / total_docs if reading_times else 0

    # Additional signals
    has_code_count = sum(1 for doc in documents if doc.get("has_code", False))
    has_images_count = sum(1 for doc in documents if doc.get("has_images", False))

    # Date range (if available)
    fetched_dates = [doc.get("fetched_at") for doc in documents if doc.get("fetched_at")]
    date_range = None
    if fetched_dates:
        fetched_dates.sort()
        date_range = (fetched_dates[0], fetched_dates[-1])

    return {
        "total_documents": total_docs,
        "word_count": {
            "average": round(avg_word_count, 2),
            "min": min_word_count,
            "max": max_word_count,
        },
        "char_count": {
            "average": round(avg_char_count, 2),
        },
        "language_distribution": dict(language_dist),
        "content_type_distribution": dict(content_type_dist),
        "reading_time": {
            "average_minutes": round(avg_reading_time, 2),
        },
        "signals": {
            "has_code": has_code_count,
            "has_images": has_images_count,
        },
        "date_range": date_range,
    }


def print_statistics(stats: Dict) -> None:
    """
    Print statistics in a readable format.

    Args:
        stats: Statistics dictionary
    """
    print("=" * 60)
    print("SCRAPING ANALYTICS")
    print("=" * 60)
    print()

    print(f"Total Documents: {stats.get('total_documents', 0)}")
    print()

    # Word count stats
    word_stats = stats.get("word_count", {})
    print("Word Count Statistics:")
    print(f"  Average: {word_stats.get('average', 0):,.0f} words")
    print(f"  Min: {word_stats.get('min', 0):,} words")
    print(f"  Max: {word_stats.get('max', 0):,} words")
    print()

    # Character count
    char_stats = stats.get("char_count", {})
    print(f"Average Character Count: {char_stats.get('average', 0):,.0f} characters")
    print()

    # Language distribution
    lang_dist = stats.get("language_distribution", {})
    if lang_dist:
        print("Language Distribution:")
        for lang, count in sorted(lang_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats["total_documents"]) * 100
            print(f"  {lang}: {count} ({percentage:.1f}%)")
        print()

    # Content type distribution
    content_dist = stats.get("content_type_distribution", {})
    if content_dist:
        print("Content Type Distribution:")
        for content_type, count in sorted(content_dist.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / stats["total_documents"]) * 100
            print(f"  {content_type}: {count} ({percentage:.1f}%)")
        print()

    # Reading time
    reading_stats = stats.get("reading_time", {})
    print(f"Average Reading Time: {reading_stats.get('average_minutes', 0):.2f} minutes")
    print()

    # Signals
    signals = stats.get("signals", {})
    print("Content Signals:")
    print(f"  Documents with code: {signals.get('has_code', 0)}")
    print(f"  Documents with images: {signals.get('has_images', 0)}")
    print()

    # Date range
    date_range = stats.get("date_range")
    if date_range:
        print(f"Date Range: {date_range[0]} to {date_range[1]}")
        print()

    print("=" * 60)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python analytics.py <jsonl_file>")
        sys.exit(1)

    file_path = sys.argv[1]
    documents = load_jsonl(file_path)
    stats = calculate_statistics(documents)
    print_statistics(stats)


if __name__ == "__main__":
    main()
