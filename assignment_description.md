# Assignment
## Take Home Assignment
We maintain an AI collections workflow that continuously gathers and cleans data to power downstream AI features (search, RAG, fine-tuning, analytics, etc.).

Your task is to design and implement a small, production-minded scraping pipeline that could plug into such a workflow.

You may use any programming language you like (Python is preferred but not required).

### Scenario
We want to collect high-quality documents from a public website and turn them into AI-ready objects with the following characteristics:

- Clean, structured text

- Rich metadata (title, URL, timestamps, tags, etc.)

- Signals that make them easy to filter and rank later (e.g., length, language, content type)

- Reasonable robustness to minor site changes

You’ll build a scraper + processor that:

1. Crawls a single public website that allows scraping (examples: a documentation site, blog, or any site that explicitly allows scraping or provides a sandbox like quotes.toscrape.com / books.toscrape.com).

2. Extracts and cleans content into a structured JSON format.

3. Enriches each record with metadata and basic quality signals.

4. Outputs a final collection we could realistically feed into an AI system.

### Requirements
1. Crawler & Fetching
Build a crawler that:

- Starts from a seed URL on your chosen domain.

- Follows internal links up to a reasonable limit (e.g., max depth or max pages).

- Avoids:

    - External domains
    - Duplicate pages
    - Obvious non-content pages (e.g., login, search results) where possible

Key performance requirements:

- Sensible throttling (e.g., small delay between requests).

- Basic error handling (timeouts, 4xx/5xx responses).

### Deliverable:

A function/CLI command like:

```bash
scrape_site --start-url=<URL> --max-pages=100 --output=output.jsonl 
```

(Exact interface is up to you; just document it.)

2. Content Extraction & Cleaning
For each page you keep in your collection:

- Extract:

    - title
    - url
    - Main body_text (not nav, footer, etc., if reasonably separable)

- Clean the text:
    - Remove boilerplate where practical
    - Normalize whitespace
    - Strip HTML tags

We don’t expect perfection, but we want to see a reasonable heuristic approach, not raw HTML dumps.

3. AI Collections Enrichment
For each document, add fields that make it more useful for AI workflows, for example:

- word_count or char_count
- language (simple heuristic is fine)
- content_type (e.g., article, doc_page, product_page – your design)
- fetched_at timestamp
- Optional: any other signals you think would help ranking, filtering, or training (e.g., estimated reading time, “is mostly code”, etc.)

### Design request:
Define a clear JSON schema for your “AI document object” (e.g., in README or as a JSON Schema file).

4. Storage & Output
- Store the final collection as newline-delimited JSON (JSONL) or a single JSON array.
- Each line/object should follow your schema consistently.
- Ensure the output is valid JSON and can be easily consumed by other tools.

5. Quality & Robustness
Show some attention to:
- Idempotency: running the script twice shouldn’t create crazy duplicates.
- Basic resilience:
    - Handle network errors.
    - Skip or log problematic pages without crashing the whole run.
- Maintainability:
    - Reasonable separation between fetching, parsing, and transforming.

We don’t need a full framework, just clear structure.

6. Documentation (Short Write-Up)
Include a short README.md that covers:

- Site chosen and why.
- How to run the scraper (dependencies, commands, configuration).
- The data schema (field names and meanings).
- Design decisions:
    - How you chose which pages to keep.
    - How you extracted “main content”.
    - How your choices support an AI collections workflow (e.g., why these metadata fields?).

If you have ideas for improving this pipeline in a real production system (e.g., scheduling, monitoring, de-dup across sources), add a short “Future Work” section.

### Optional Bonus Tasks (Nice-to-Have, Not Required)
- Tests (unit tests for your parsing/transform functions).
- Configurable filters:
    - e.g., only scrape URLs matching a certain pattern (/docs/).
- Simple analytics:
    - e.g., a small script/notebook that loads the output and prints stats (number of docs, avg length, language distribution).
- Dockerfile to run the scraper in a container.

### Evaluate keypoints:
We’re primarily looking at:
- Correctness & reliability
    - Does it run and produce a sane collection of documents?
- Code quality
    - Readability, structure, naming, comments where needed.
- Scraping & parsing approach
    - How thoughtfully you handle crawling, extraction, and cleaning.
- AI workflow awareness
    - Is the output realistically useful as input to an AI system (RAG, search, training)? Does the schema + metadata make sense?
- Documentation
    - Can someone else understand and run your project quickly?