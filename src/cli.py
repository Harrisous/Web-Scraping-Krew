"""Command-line interface for the web scraping pipeline with async support."""

import logging
import sys
import asyncio
from pathlib import Path
from typing import Optional
import click
from tqdm import tqdm

from .url_collector import URLCollector
from .async_fetcher import AsyncFetcher
from .extractor import Extractor
from .enricher import Enricher
from .keyword_extractor import KeywordExtractor
from .writer import Writer

# Configure logging to stderr to avoid interfering with tqdm progress bar
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)

# Suppress httpx's verbose HTTP request logging to keep progress bar clean
logging.getLogger("httpx").setLevel(logging.WARNING)


async def process_urls_async(
    urls: list[str],
    extractor: Extractor,
    enricher: Enricher,
    keyword_extractor: KeywordExtractor,
    writer: Writer,
    max_concurrent: int = 10,
    delay: float = 0.1,
) -> tuple[int, int, int]:
    """
    Process URLs asynchronously: fetch, extract, enrich, and write.

    Args:
        urls: List of URLs to process
        extractor: Content extractor instance
        enricher: Metadata enricher instance
        keyword_extractor: Keyword extractor instance
        writer: Output writer instance
        max_concurrent: Maximum concurrent requests
        delay: Delay between requests

    Returns:
        Tuple of (successful, failed, skipped) counts
    """
    successful = 0
    failed = 0
    skipped = 0

    # Filter out URLs that should be skipped
    urls_to_process = [url for url in urls if not writer.should_skip(url)]
    skipped = len(urls) - len(urls_to_process)

    if not urls_to_process:
        return (successful, failed, skipped)

    logger.info(f"Phase 2: Processing {len(urls_to_process)} URLs with {max_concurrent} concurrent workers...")

    # Progress bar
    pbar = tqdm(total=len(urls_to_process), desc="Processing pages", unit="page", file=sys.stdout)

    async with AsyncFetcher(max_concurrent=max_concurrent, delay=delay) as fetcher:
        # Fetch all URLs concurrently
        results = await fetcher.fetch_batch(urls_to_process)

        # Process results
        for url, response in results:
            pbar.update(1)

            if response is None:
                failed += 1
                pbar.set_postfix({"success": successful, "failed": failed, "skipped": skipped})
                continue

            try:
                # Extract content
                extracted = extractor.extract(response.text, url)
                if not extracted.get("body_text"):
                    logger.debug(f"No content extracted from {url}")
                    failed += 1
                    pbar.set_postfix({"success": successful, "failed": failed, "skipped": skipped})
                    continue

                # Extract keywords
                keywords = keyword_extractor.extract(
                    title=extracted["title"],
                    body_text=extracted["body_text"],
                )

                # Enrich document
                enriched = enricher.enrich(
                    title=extracted["title"],
                    body_text=extracted["body_text"],
                    url=url,
                    images=extracted.get("images", []),
                )

                # Combine into final document
                document = {
                    "title": extracted["title"],
                    "url": url,
                    "body_text": extracted["body_text"],
                    "keywords": keywords,
                    **enriched,
                }

                # Write document
                if writer.write(document):
                    successful += 1
                else:
                    failed += 1

                pbar.set_postfix({"success": successful, "failed": failed, "skipped": skipped})

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed += 1
                pbar.set_postfix({"success": successful, "failed": failed, "skipped": skipped})

    pbar.close()
    return (successful, failed, skipped)


@click.command()
@click.option(
    "--start-url",
    required=True,
    help="Starting URL for crawling",
)
@click.option(
    "--max-pages",
    default=100,
    type=int,
    help="Maximum number of pages to scrape (default: 100)",
)
@click.option(
    "--max-depth",
    default=3,
    type=int,
    help="Maximum crawling depth (default: 3)",
)
@click.option(
    "--output",
    default="output.jsonl",
    help="Output JSONL file path (default: output.jsonl)",
)
@click.option(
    "--delay",
    default=0.1,
    type=float,
    help="Delay between requests in seconds (default: 0.1)",
)
@click.option(
    "--url-pattern",
    default=None,
    help="Optional regex pattern to filter URLs (e.g., '/books/')",
)
@click.option(
    "--resume",
    is_flag=True,
    help="Resume mode: skip URLs already in output file",
)
@click.option(
    "--max-concurrent",
    default=10,
    type=int,
    help="Maximum concurrent requests in phase 2 (default: 10)",
)
@click.option(
    "--timestamp",
    is_flag=True,
    help="Enable timestamped output filenames (appends hash to filename)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
def scrape_site(
    start_url: str,
    max_pages: int,
    max_depth: int,
    output: str,
    delay: float,
    url_pattern: Optional[str],
    resume: bool,
    max_concurrent: int,
    timestamp: bool,
    verbose: bool,
):
    """
    Scrape a website and output AI-ready documents in JSONL format.

    Uses a two-phase approach:
    1. Phase 1: Collect all URLs by crawling (sequential)
    2. Phase 2: Fetch and process content concurrently (async)

    Example:
        scrape_site --start-url=https://web-scraping.dev --max-pages=50 --max-concurrent=20
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting scrape of {start_url}")
    logger.info(f"Max pages: {max_pages}, Max depth: {max_depth}, Max concurrent: {max_concurrent}")

    try:
        # Phase 1: Collect URLs
        collector = URLCollector(
            start_url=start_url,
            max_pages=max_pages,
            max_depth=max_depth,
            url_pattern=url_pattern,
            delay=delay,
        )
        urls = collector.collect_all_urls()

        if not urls:
            logger.warning("No URLs collected!")
            return

        logger.info(f"Collected {len(urls)} URLs for processing")

        # Initialize processing components
        extractor = Extractor()
        enricher = Enricher()
        keyword_extractor = KeywordExtractor()
        writer = Writer(output_path=output, resume=resume, use_timestamp=timestamp)

        logger.info(f"Output file: {writer.output_path}")

        # Phase 2: Process URLs asynchronously
        successful, failed, skipped = asyncio.run(
            process_urls_async(
                urls=urls,
                extractor=extractor,
                enricher=enricher,
                keyword_extractor=keyword_extractor,
                writer=writer,
                max_concurrent=max_concurrent,
                delay=delay,
            )
        )

        # Summary
        logger.info("=" * 60)
        logger.info("Scraping completed!")
        logger.info(f"URLs collected: {len(urls)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Skipped: {skipped}")
        logger.info(f"Total written: {writer.get_written_count()}")
        logger.info(f"Output file: {writer.output_path}")
        logger.info("=" * 60)

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    scrape_site()
