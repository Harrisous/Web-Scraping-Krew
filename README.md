# Web Scraping Pipeline for AI Collections

A production-minded web scraping pipeline designed to collect high-quality documents from public websites and transform them into AI-ready objects with clean, structured text and rich metadata.

## Site Chosen

**books.toscrape.com** - A practice website designed for web scraping exercises.

**Why this site?**
- Explicitly allows scraping (designed for this purpose)
- Well-structured HTML with clear content patterns
- Diverse content types (product pages, category pages, homepage)
- Good for demonstrating content extraction and classification
- No authentication or complex JavaScript requirements

## Features

- **Intelligent Crawling**: Follows internal links with depth control and deduplication
- **Content Extraction**: Extracts main content while removing navigation, footers, and ads
- **AI Enrichment**: Adds metadata useful for AI workflows (language, content type, reading time, etc.)
- **Idempotency**: Resume mode to skip already-scraped URLs
- **Error Handling**: Robust error handling with retries and graceful degradation
- **Configurable Filters**: URL pattern filtering for targeted scraping
- **Analytics**: Built-in analytics script for data insights

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd Web-Scraping-Krew
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package (optional, for CLI command):**
   ```bash
   pip install -e .
   ```

## Usage

### Basic Usage

```bash
scrape_site --start-url=https://books.toscrape.com --max-pages=50 --output=books.jsonl
```

### Advanced Usage

```bash
# With custom depth and delay
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=100 \
  --max-depth=3 \
  --delay=1.5 \
  --output=books.jsonl

# With URL pattern filtering (only scrape /books/ pages)
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --url-pattern="/books/" \
  --output=books.jsonl

# Resume mode (skip already scraped URLs)
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=100 \
  --output=books.jsonl \
  --resume

# Verbose logging
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --output=books.jsonl \
  --verbose
```

### Command-Line Options

- `--start-url` (required): Starting URL for crawling
- `--max-pages` (default: 100): Maximum number of pages to scrape
- `--max-depth` (default: 3): Maximum crawling depth
- `--output` (default: output.jsonl): Output JSONL file path
- `--delay` (default: 1.0): Delay between requests in seconds
- `--url-pattern`: Optional regex pattern to filter URLs
- `--resume`: Skip URLs already in output file (idempotency)
- `--verbose` / `-v`: Enable verbose logging

## Data Schema

Each document in the JSONL output follows this schema:

```json
{
  "title": "string - Page title",
  "url": "string - Full URL of the page",
  "body_text": "string - Cleaned main content text",
  "word_count": "integer - Number of words",
  "char_count": "integer - Number of characters",
  "language": "string - ISO 639-1 language code (e.g., 'en', 'fr')",
  "content_type": "string - Classification: 'product_page', 'doc_page', 'article', 'homepage', 'listing_page', 'other'",
  "fetched_at": "string - ISO 8601 timestamp (UTC)",
  "reading_time_minutes": "number - Estimated reading time in minutes",
  "has_code": "boolean - Whether content likely contains code",
  "has_images": "boolean - Whether page contains images (currently always false)"
}
```

### Schema Fields Explained

- **title**: Extracted from `<title>`, `<h1>`, or `og:title` meta tag
- **url**: Canonical URL of the scraped page
- **body_text**: Main content with HTML tags removed, navigation/footer excluded
- **word_count**: Total word count (title + body)
- **char_count**: Total character count (title + body)
- **language**: Detected using `langdetect` library
- **content_type**: Heuristic classification based on URL patterns and content
- **fetched_at**: Timestamp when the page was fetched (UTC)
- **reading_time_minutes**: Based on 200 words per minute reading speed
- **has_code**: Detects code-like patterns (functions, classes, imports, etc.)
- **has_images**: Placeholder for future image detection

## Design Decisions

### Content Extraction Strategy

1. **Main Content Identification**:
   - Prioritizes `<main>` or `<article>` tags
   - Falls back to content containers with common class names
   - Removes navigation, headers, footers, scripts, and styles

2. **Text Cleaning**:
   - Strips HTML tags
   - Normalizes whitespace (multiple spaces → single space)
   - Removes excessive newlines
   - Preserves paragraph structure

### Page Filtering Logic

Pages are filtered out if they match:
- Login/signup pages (`/login`, `/signup`, etc.)
- Search result pages (`/search?`)
- Cart/checkout pages
- File downloads (PDF, images, etc.)
- External domains
- URLs matching skip patterns

### Metadata Choices for AI Workflows

The metadata fields are designed to support:

1. **Filtering**: Language, content_type, word_count for quality filtering
2. **Ranking**: Reading time, word count for relevance scoring
3. **Training**: Content type and language for dataset curation
4. **RAG Systems**: Clean text, metadata for chunking and retrieval
5. **Analytics**: Timestamps, content types for monitoring and insights

## Analytics

Use the analytics script to analyze your scraped data:

```bash
python scripts/analytics.py output.jsonl
```

This will print:
- Total document count
- Word/character count statistics
- Language distribution
- Content type distribution
- Average reading time
- Content signals (code, images)
- Date range

## Testing

Run tests with pytest:

```bash
# Install in development mode first
pip install -e .

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_extractor.py
```

## Docker

Build and run with Docker:

```bash
# Build image
docker build -t web-scraper .

# Run scraper
docker run --rm \
  -v $(pwd):/app/output \
  web-scraper \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --output=/app/output/books.jsonl
```

## Project Structure

```
Web-Scraping-Krew/
├── src/
│   ├── __init__.py
│   ├── crawler.py          # URL crawling and queue management
│   ├── fetcher.py          # HTTP fetching with throttling
│   ├── extractor.py        # Content extraction and cleaning
│   ├── enricher.py         # AI metadata enrichment
│   ├── writer.py           # JSONL output with idempotency
│   └── cli.py              # Command-line interface
├── tests/
│   ├── test_crawler.py
│   ├── test_extractor.py
│   └── test_enricher.py
├── scripts/
│   └── analytics.py        # Analytics script
├── requirements.txt
├── setup.py
├── Dockerfile
└── README.md
```

## Future Work

For a production system, consider:

1. **Scheduling**: Integrate with task schedulers (Celery, Airflow) for periodic scraping
2. **Monitoring**: Add metrics collection (Prometheus, Datadog) for crawl health
3. **Distributed Crawling**: Scale across multiple workers/nodes
4. **Deduplication**: Cross-source deduplication using content hashing
5. **Change Detection**: Track content changes over time
6. **Rate Limiting**: Respect robots.txt and implement adaptive rate limiting
7. **Storage Backends**: Support for databases (PostgreSQL, MongoDB) in addition to JSONL
8. **JavaScript Rendering**: Add Selenium/Playwright for JavaScript-heavy sites
9. **Content Validation**: Quality scoring and validation pipelines
10. **API Integration**: REST API for triggering and monitoring scrapes

## License

See LICENSE file for details.
