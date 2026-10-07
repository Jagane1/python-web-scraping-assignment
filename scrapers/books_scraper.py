"""Books to Scrape: selectors and parsing only."""
from __future__ import annotations

from urllib.parse import urljoin

import config
from scrapers.base_scraper import BaseScraper


class BooksScraper(BaseScraper):
    source_name = config.BOOKS_SOURCE
    start_url = config.BOOKS_START_URL

    def __init__(self, *args, fetch_details: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.fetch_details = fetch_details
        self.stats["detail_failures"] = 0

    def parse_page(self, soup, page_url):
        items = soup.select("article.product_pod")
        return self.parse_each(items, self.parse_listing_item, page_url)

    def parse_listing_item(self, article, page_url: str) -> dict:
        link = article.select_one("h3 > a")
        price = article.select_one("p.price_color")
        rating = article.select_one("p.star-rating")
        availability = article.select_one("p.availability")
        raw = {
            "title": link.get("title") if link else None,       # full title; visible text is truncated
            "url": urljoin(page_url, link["href"]) if link and link.get("href") else None,
            "price_raw": price.get_text() if price else None,
            "rating_raw": " ".join(rating.get("class", [])) if rating else None,
            "availability_raw": availability.get_text() if availability else None,
            "category_raw": None,
            "description_raw": None,
        }
        if self.fetch_details and raw["url"]:
            self.add_detail(raw)
        return raw

    def add_detail(self, raw: dict) -> None:
        """Visit the detail page for category/description. Failure leaves them empty."""
        soup = self.fetch(raw["url"])
        if soup is None:
            self.stats["detail_failures"] += 1
            return
        raw.update({k: v for k, v in self.parse_detail(soup).items() if v is not None})

    @staticmethod
    def parse_detail(soup) -> dict:
        crumbs = soup.select("ul.breadcrumb li a")             # Home > Books > <Category>
        header = soup.select_one("#product_description")
        description = header.find_next_sibling("p") if header else None
        availability = soup.select_one("p.availability")
        return {
            "category_raw": crumbs[2].get_text() if len(crumbs) >= 3 else None,
            "description_raw": description.get_text() if description else None,
            "availability_raw": availability.get_text() if availability else None,
        }
