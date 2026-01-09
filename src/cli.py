"""Command-line interface for the web scraping pipeline."""

import logging
import sys
from pathlib import Path
import click
from tqdm import tqdm

from .crawler import Crawler
from .fetcher import Fetcher
from .extractor import Extractor
from .enricher import Enricher
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
    default=1.0,
    type=float,
    help="Delay between requests in seconds (default: 1.0)",
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
    url_pattern: str,
    resume: bool,
    verbose: bool,
):
    """
    Scrape a website and output AI-ready documents in JSONL format.

    Example:
        scrape_site --start-url=https://books.toscrape.com --max-pages=50 --output=books.jsonl
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting scrape of {start_url}")
    logger.info(f"Max pages: {max_pages}, Max depth: {max_depth}, Output: {output}")

    # Initialize components
    crawler = Crawler(
        start_url=start_url,
        max_pages=max_pages,
        max_depth=max_depth,
        url_pattern=url_pattern,
    )

    fetcher = Fetcher(delay=delay)
    extractor = Extractor()
    enricher = Enricher()
    writer = Writer(output_path=output, resume=resume)

    # Progress tracking
    successful = 0
    failed = 0
    skipped = 0

    try:
        # Progress bar with continuous updates
        with tqdm(
            total=max_pages,
            desc="Scraping pages",
            unit="page",
            file=sys.stdout,
            dynamic_ncols=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}{postfix}]"
        ) as pbar:
            while True:
                # Get next URL
                result = crawler.get_next_url()
                if result is None:
                    break

                url, current_depth = result

                # Check if should skip (resume mode)
                if writer.should_skip(url):
                    skipped += 1
                    pbar.update(1)
                    continue

                # Fetch page
                response = fetcher.fetch(url)
                if response is None:
                    failed += 1
                    pbar.update(1)
                    continue

                # Extract content
                extracted = extractor.extract(response.text, url)
                if not extracted.get("body_text"):
                    logger.warning(f"No content extracted from {url}")
                    failed += 1
                    pbar.update(1)
                    continue

                # Add links to crawler queue
                crawler.add_links(url, response.text, current_depth)

                # Enrich document
                enriched = enricher.enrich(
                    title=extracted["title"],
                    body_text=extracted["body_text"],
                    url=url,
                )

                # Combine into final document
                document = {
                    "title": extracted["title"],
                    "url": url,
                    "body_text": extracted["body_text"],
                    **enriched,
                }

                # Write document
                if writer.write(document):
                    successful += 1
                else:
                    failed += 1

                pbar.update(1)
                pbar.set_postfix(
                    {
                        "success": successful,
                        "failed": failed,
                        "skipped": skipped,
                        "queued": len(crawler.queue),
                    }
                )

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        fetcher.close()

    # Summary
    logger.info("=" * 60)
    logger.info("Scraping completed!")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped: {skipped}")
    logger.info(f"Total written: {writer.get_written_count()}")
    logger.info(f"Output file: {output}")
    logger.info("=" * 60)


if __name__ == "__main__":
    scrape_site()
