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
- Perfect for learning and testing web scraping techniques
- Includes product images, tables, and structured data

## Features

- **Two-Phase Workflow**: Efficient URL collection followed by parallel content fetching
- **Async/Concurrent Processing**: High-performance async fetching with configurable concurrency
- **Modern Web Design Support**: Enhanced extractor handles flex layouts, modern CSS patterns, and complex HTML structures
- **Intelligent Crawling**: Follows internal links with depth control and deduplication
- **Content Extraction**: Extracts main content while removing navigation, footers, and ads (improved for modern sites)
- **AI Enrichment**: Adds metadata useful for AI workflows (language, content type, reading time, etc.)
- **Timestamped Output**: Automatic timestamped output files with hash-based naming
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
# Uses default output file: output.jsonl
scrape_site --start-url=https://web-scraping.dev --max-pages=50

# Specify custom output file
scrape_site --start-url=https://web-scraping.dev --max-pages=50 --output=custom.jsonl

# Enable timestamped output (appends hash: output_a1b2c3d4.jsonl)
scrape_site --start-url=https://web-scraping.dev --max-pages=50 --timestamp
```

### Advanced Usage

```bash
# High-performance scraping with concurrent requests
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=100 \
  --max-concurrent=20 \
  --delay=0.1

# With URL pattern filtering (only scrape /catalogue/ pages)
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --url-pattern="/catalogue/" \
  --max-concurrent=15

# Resume mode (skip already scraped URLs)
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=100 \
  --resume

# Enable timestamped output (appends hash to filename)
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --output=output.jsonl \
  --timestamp

# Verbose logging
scrape_site \
  --start-url=https://books.toscrape.com \
  --max-pages=50 \
  --verbose
```

### Command-Line Options

- `--start-url` (required): Starting URL for crawling
- `--max-pages` (default: 100): Maximum number of pages to scrape
- `--max-depth` (default: 3): Maximum crawling depth
- `--output` (default: output.jsonl): Output JSONL file path
- `--delay` (default: 0.1): Delay between requests in seconds (phase 2)
- `--url-pattern`: Optional regex pattern to filter URLs
- `--resume`: Skip URLs already in output file (idempotency)
- `--max-concurrent` (default: 10): Maximum concurrent requests in phase 2
- `--timestamp`: Enable timestamped output filenames (appends hash to filename)
- `--verbose` / `-v`: Enable verbose logging

### Two-Phase Workflow

The scraper uses an optimized two-phase approach:

1. **Phase 1 - URL Collection**: Sequentially crawls the site to discover all URLs (with throttling)
2. **Phase 2 - Content Processing**: Concurrently fetches and processes content using async I/O

This approach maximizes performance while respecting rate limits during discovery.

## Data Schema

Each document in the JSONL output follows this schema:

```json
{
  "title": "string - Page title",
  "url": "string - Full URL of the page",
  "body_text": "string - Cleaned main content text",
  "keywords": "array[string] - Extracted keywords/phrases (up to 10)",
  "word_count": "integer - Number of words",
  "char_count": "integer - Number of characters",
  "language": "string - ISO 639-1 language code (e.g., 'en', 'fr')",
  "content_type": "string - Classification: 'product_page', 'doc_page', 'article', 'homepage', 'listing_page', 'other'",
  "fetched_at": "string - ISO 8601 timestamp (UTC)",
  "reading_time_minutes": "number - Estimated reading time in minutes",
  "images": "array[string] - List of absolute image URLs found on the page"
}
```

### Schema Fields Explained

- **title**: Extracted from `<title>`, `<h1>`, or `og:title` meta tag
- **url**: Canonical URL of the scraped page
- **body_text**: Main content with HTML tags removed, navigation/footer excluded. For listing pages, includes all items (not just the first)
- **keywords**: Array of extracted keywords/phrases using RAKE algorithm (up to 10 keywords)
- **word_count**: Total word count (title + body)
- **char_count**: Total character count (title + body)
- **language**: Detected using `langdetect` library
- **content_type**: Heuristic classification based on URL patterns and content
- **fetched_at**: Timestamp when the page was fetched (UTC)
- **reading_time_minutes**: Based on 200 words per minute reading speed
- **images**: Array of absolute image URLs extracted from the page (includes `src`, `srcset`, `data-src`, and background images)

## Design Decisions

### Content Extraction Strategy

1. **Main Content Identification** (Enhanced for modern web design):
   - Prioritizes semantic HTML5 elements (`<main>`, `<article>`)
   - Uses ARIA role attributes (`role="main"`, `role="article"`)
   - Tries common content class names and data attributes
   - Falls back to heuristic: finds largest text container (useful for flex/grid layouts)
   - Removes navigation, headers, footers, scripts, styles, modals, popups, cookie banners

2. **Table Extraction**:
   - Extracts all table content from `<table>` elements
   - Preserves table structure with pipe separators (|)
   - Includes both `<thead>` and `<tbody>` content
   - Formats tables as readable text for AI processing

3. **Image Extraction**:
   - Extracts images from `<img src="">` attributes
   - Handles responsive images via `srcset` attribute
   - Supports lazy-loaded images (`data-src`, `data-lazy-src`)
   - Extracts background images from CSS `style` attributes
   - Resolves relative URLs to absolute URLs
   - Filters out data URIs and icon files (.ico, .svg)

4. **Text Cleaning** (Improved):
   - Strips HTML tags
   - Removes invisible Unicode characters (prevents AI obfuscation issues)
   - Normalizes whitespace (multiple spaces → single space)
   - Removes excessive newlines
   - Removes common flex layout artifacts (pipe separators, bullets)
   - Preserves paragraph structure

5. **Keyword Extraction**:
   - Uses RAKE (Rapid Automatic Keyword Extraction) algorithm
   - Extracts up to 10 keywords/phrases per page
   - Filters stop words and short terms
   - Optimized for AI workflows and search indexing

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
