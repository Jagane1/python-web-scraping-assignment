"""Quotes to Scrape: selectors and parsing only."""
from __future__ import annotations

import config
from scrapers.base_scraper import BaseScraper


class QuotesScraper(BaseScraper):
    source_name = config.QUOTES_SOURCE
    start_url = config.QUOTES_START_URL

    def parse_page(self, soup, page_url):
        return self.parse_each(soup.select("div.quote"), self.parse_quote, page_url)

    @staticmethod
    def parse_quote(div, page_url: str) -> dict:
        text = div.select_one("span.text")
        author = div.select_one("small.author")
        return {
            "text_raw": text.get_text() if text else None,
            "author_raw": author.get_text() if author else None,
            "tags_raw": [t.get_text() for t in div.select("div.tags a.tag")],  # may be empty
            "page_url": page_url,
        }
