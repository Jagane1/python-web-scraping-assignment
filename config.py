"""Central settings. Change values here instead of hunting through the code."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"

BOOKS_SOURCE = "Books to Scrape"
QUOTES_SOURCE = "Quotes to Scrape"
VALID_SOURCES = {BOOKS_SOURCE, QUOTES_SOURCE}

BOOKS_START_URL = "https://books.toscrape.com/"
QUOTES_START_URL = "https://quotes.toscrape.com/"

USER_AGENT = "ScrapingAssignment/1.0 (learning project)"
REQUEST_DELAY = 0.5      # seconds to pause after every request
REQUEST_TIMEOUT = 10     # seconds before a request is abandoned
MAX_RETRIES = 3          # retries for temporary errors
BACKOFF_FACTOR = 1.0     # retry waits grow: 1s, 2s, 4s
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]

# Fixed CSV column order (every row has every column; N/A fields stay empty).
COLUMNS = [
    "source", "source_url", "name_or_title", "category", "price", "rating",
    "author", "tags", "description", "availability", "scraped_at",
]

QUOTE_FINGERPRINT_CHARS = 50   # quote text characters used for duplicate detection
