# Multi-Source Web Scraping & Data Consolidation

A small ETL pipeline that scrapes Books to Scrape (~1,000 books, 50 pages) and Quotes to Scrape
(100 quotes, 10 pages), cleans and validates the records, removes duplicates, and writes one consolidated
CSV, a JSON summary and a log file.

```
Scrape (both sites) -> Clean -> Validate -> Deduplicate -> Consolidate -> Save files
```

## Python version & dependencies
Python 3.10 – 3.12 (developed on 3.12). Libraries: `requests`, `beautifulsoup4`, `lxml`, `pytest` (tests only).
Everything else is the standard library.

## Setup
```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run
```bash
python main.py                    # full run (visits every book page: ~1,100 requests, roughly 10-15 min)
python main.py --skip-details     # fast run (~60 requests): book category/description left empty
python main.py --max-pages 2      # quick sanity check
python -m pytest                  # unit tests, no internet needed
```
Options: `--delay SECONDS` (default 0.5), `--max-pages N`, `--skip-details`, `--output-dir PATH`.
Exit code is `1` if nothing at all was collected.

## Output
| File | Contents |
| --- | --- |
| `output/final_dataset.csv` | One row per valid, unique record; identical columns for every row (UTF-8) |
| `output/summary_report.json` | Per source: pages scraped/failed, collected, cleaned, rejected (by reason), duplicates, final count; totals; run time; `counts_reconcile` |
| `logs/scraper.log` | Every page, warning (rejected record, duplicate) and error (failed request) |

`collected - rejected - duplicates = final` always holds and is checked in the report (`counts_reconcile`).
A record with several validation problems counts once in `rejected_total` but once per reason in `rejected_by_reason`.

## Step 1 – Source observations
| Item | Books to Scrape | Quotes to Scrape |
| --- | --- | --- |
| One record | `article.product_pod` | `div.quote` |
| Main text | `h3 > a` — full title is in the `title` attribute (visible text is truncated with `...`) | `span.text` wrapped in curly quotes |
| Price / rating | `p.price_color` (`£51.77`); class on `p.star-rating` (`Three`) | none |
| Author / tags | none | `small.author`; `div.tags a.tag` (zero or more) |
| Category / description | only on the detail page (breadcrumb 3rd link; `#product_description + p`) | none |
| Link | `h3 > a[href]` – *relative* and differs per page (`catalogue/...` from home, bare from `catalogue/page-N.html`) | author link only |
| Next page | `li.next > a` (relative) | `li.next > a` (relative, `/page/2/`) |

## How pagination works
`BaseScraper.scrape()` starts at the home page, parses it, looks for `li.next > a[href]`, turns the relative
link into a full URL with `urljoin`, and repeats until no link exists. No page numbers are hard-coded. A
`visited` set stops an accidental loop. If a page cannot be fetched after retries, that source stops (the
failed page is the only place the next link lives) and the other source still runs.

## Data model
| Column | Books | Quotes |
| --- | --- | --- |
| `source` | Books to Scrape | Quotes to Scrape |
| `source_url` | book detail page URL | URL of the listing page the quote appeared on |
| `name_or_title` | full title | quote text without the surrounding quote marks |
| `category` | from detail page | empty |
| `price` | float (e.g. 51.77) | empty |
| `rating` | int 1–5 | empty |
| `author` | empty | author name |
| `tags` | empty | lowercase, unique, sorted, `;`-joined |
| `description` | from detail page (may be empty) | empty |
| `availability` | e.g. `In stock (22 available)` | empty |
| `scraped_at` | UTC ISO timestamp | UTC ISO timestamp |

One flat table was chosen because the assignment asks for one CSV; fields that do not apply stay empty, never
invented (e.g. quotes do not get a price of 0). `availability` is an extra column for books (the assignment
lists availability among the book fields). Quote `source_url` is the listing page (each quote has no page of its
own); the author page was the alternative.

## Cleaning approach (`processing/cleaning.py`, `processing/normalize.py`)
Small pure functions, tested with plain strings: `clean_text` (collapses spaces/tabs/newlines/`\xa0`),
`strip_quotes`, `clean_price` (`£51.77` -> `51.77`), `clean_rating` (`Three` -> `3`), `clean_tags`,
`normalize_url`. "Nothing usable" is always `None`. Pages are decoded as UTF-8 so `£` is not corrupted.
Scrapers return raw text; `normalize.py` maps raw dicts onto the data model, so a layout change only touches a scraper.

## Validation approach (`processing/validation.py`)
Returns a list of reasons: `unknown_source`, `missing_name`, `invalid_url`, `invalid_price` (must be a number >= 0),
`invalid_rating` (integer 1–5), `missing_author` (quotes only). Invalid records are logged as warnings, counted by
reason and excluded; the run continues. Cleaning exceptions are counted as `normalization_error`.

## Deduplication approach (`processing/deduplication.py`)
Each record gets a SHA-256 fingerprint of its identifying fields, each lowercased, stripped of punctuation and
whitespace-collapsed first:
- Books: source + title + price
- Quotes: source + author + first 50 characters of the (normalised) quote text

Records whose fingerprint was already seen are duplicates. I 7ygvcfh\remove them (first occurrence is kept) instead of
flagging, because the output is meant to be an analysis-ready table; every removal is logged and the count and
examples are in the summary. "Lesson from the real run: my first rule was source + title only, and it wrongly merged two genuinely different books both titled 'The Star-Touched Queen' (listed at £46.02 and £32.30, with different product URLs). Adding the price fixed it, and the real run keeps both. The sites contain no true duplicates, so duplicates_detected is 0 on a real run; the logic is proven by unit tests with deliberately duplicated data. Limitation: two different books with the same title and the same price would still be merged."

## Error-handling approach
- Requests: one `requests.Session` with User-Agent, 10 s timeout, and automatic retries with exponential
  backoff (1 s, 2 s, 4 s) for HTTP 429/500/502/503/504 and connection errors.
- HTTP/timeouts/connection errors: caught per request, logged at ERROR, scraping continues where possible.
- Missing elements: every `select_one` result is checked for `None`; fields become `None`.
- One bad record / page: wrapped in `try/except`, logged, skipped.
- Book detail page fails: the book is kept, with category/description empty.
- A whole source fails: isolated in `process_source`; the other source still runs and the report records it.
- Politeness: 0.5 s pause after every request; only the two practice sites are contacted; no protection is bypassed.

## Project structure
```
main.py            CLI entry point + logging setup
pipeline.py        orchestration: stages, CSV/JSON writers, summary metrics
config.py          URLs, delays, columns, constants
scrapers/          base_scraper.py (session, retries, pagination), books_scraper.py, quotes_scraper.py
processing/        cleaning.py, normalize.py, validation.py, deduplication.py
tests/             offline unit tests + a fake website (conftest_helpers.py)
```
`pipeline.py` and `normalize.py` are small additions to the recommended layout so `main.py` stays a thin entry point.

## Assumptions
- Both sites keep their current HTML structure. - Book title = `title` attribute of `h3 > a`.
- A book is identified by title (the site has no ISBN-style id on the listing). - Prices are GBP (`£`) and stored as plain numbers.

## Known limitations
- Sequential scraping (a full run with details takes ~10–15 minutes); no checkpoint/resume.
- If a listing page fails after retries, later pages of that source are not scraped.
- `robots.txt` is not parsed programmatically (the practice sites impose no restrictions).
- Production changes I would make: scheduling, checkpointing, concurrency with a rate limiter, alerting on count drops, storing results in a database.


## AI usage summary
I used AI tools (Claude chat and the Claude Code assistant in VS Code) to design the project structure and draft the scrapers, cleaning, validation, deduplication, pipeline and tests. I reviewed the code, ran the full pipeline myself, and found and fixed a bug in the AI's first deduplication rule: it treated two different books with the same title ("The Star-Touched Queen", £46.02 and £32.30) as duplicates. The fix was to include the price in the book fingerprint. A unit test also caught a tag-lowercasing bug in the AI's code. The final run produced 1,100 rows with 0 duplicates and 29 passing tests. Full details are in `AI_USAGE.md`.
