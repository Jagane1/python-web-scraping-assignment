"""Shared networking + pagination loop. Source-specific parsing lives in subclasses."""
from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

import config


def create_session() -> requests.Session:
    """Session with a User-Agent and automatic retries (exponential backoff)."""
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    retries = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.BACKOFF_FACTOR,
        status_forcelist=config.RETRY_STATUS_CODES,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class BaseScraper(ABC):
    source_name: str
    start_url: str

    def __init__(self, session=None, delay: float = config.REQUEST_DELAY,
                 timeout: float = config.REQUEST_TIMEOUT, max_pages: int | None = None):
        self.session = session or create_session()
        self.delay = delay
        self.timeout = timeout
        self.max_pages = max_pages
        self.logger = logging.getLogger(type(self).__name__)
        self.stats = {"pages_scraped": 0, "pages_failed": 0, "record_errors": 0}

    # ---- networking -------------------------------------------------------
    def fetch(self, url: str) -> BeautifulSoup | None:
        """Download and parse one page. Returns None (and logs) on any failure."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()                # raises on 404, 500, ...
            response.encoding = "utf-8"                # keeps £ correct
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as exc:       # timeouts, connection, HTTP errors
            self.logger.error("Failed to fetch %s: %s", url, exc)
            return None
        finally:
            time.sleep(self.delay)                     # be polite to the server

    # ---- pagination -------------------------------------------------------
    @staticmethod
    def next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
        link = soup.select_one("li.next > a[href]")
        return urljoin(current_url, link["href"]) if link else None

    def scrape(self) -> list[dict]:
        """Follow the 'next' link until there is none; return raw records."""
        records: list[dict] = []
        visited: set[str] = set()                      # guards against a looping 'next' link
        url: str | None = self.start_url
        page = 0
        while url and url not in visited:
            if self.max_pages and page >= self.max_pages:
                self.logger.info("[%s] reached max_pages=%d, stopping", self.source_name, self.max_pages)
                break
            visited.add(url)
            page += 1
            self.logger.info("[%s] page %d: %s", self.source_name, page, url)

            soup = self.fetch(url)
            if soup is None:
                self.stats["pages_failed"] += 1
                self.logger.error("[%s] page failed; no next link available, stopping this source", self.source_name)
                break
            try:
                page_records = self.parse_page(soup, url)
            except Exception:                          # unexpected layout: skip the page, keep going
                self.stats["pages_failed"] += 1
                self.logger.exception("[%s] could not parse %s", self.source_name, url)
                page_records = []
            records.extend(page_records)
            self.stats["pages_scraped"] += 1
            url = self.next_page_url(soup, url)

        self.logger.info("[%s] finished: %d raw records from %d pages", self.source_name, len(records), page)
        return records

    # ---- helpers for subclasses ------------------------------------------
    def parse_each(self, elements, parse_fn, page_url: str) -> list[dict]:
        """Run parse_fn on every element; log and skip any single record that blows up."""
        out = []
        for index, element in enumerate(elements, start=1):
            try:
                out.append(parse_fn(element, page_url))
            except Exception as exc:
                self.stats["record_errors"] += 1
                self.logger.warning("[%s] skipped record #%d on %s: %s", self.source_name, index, page_url, exc)
        return out

    @abstractmethod
    def parse_page(self, soup: BeautifulSoup, page_url: str) -> list[dict]:
        """Return raw dicts (text exactly as found) for every record on the page."""
