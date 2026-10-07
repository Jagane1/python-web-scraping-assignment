"""Turn a raw scraped dict (text exactly as found) into the common data model."""
from __future__ import annotations

import config
from processing.cleaning import (
    clean_price, clean_rating, clean_tags, clean_text, normalize_url, strip_quotes,
)


def normalize_book(raw: dict, scraped_at: str) -> dict:
    return {
        "source": config.BOOKS_SOURCE,
        "source_url": normalize_url(raw.get("url")),
        "name_or_title": clean_text(raw.get("title")),
        "category": clean_text(raw.get("category_raw")),
        "price": clean_price(raw.get("price_raw")),
        "rating": clean_rating(raw.get("rating_raw")),
        "author": None,
        "tags": None,
        "description": clean_text(raw.get("description_raw")),
        "availability": clean_text(raw.get("availability_raw")),
        "scraped_at": scraped_at,
    }


def normalize_quote(raw: dict, scraped_at: str) -> dict:
    return {
        "source": config.QUOTES_SOURCE,
        "source_url": normalize_url(raw.get("page_url")),
        "name_or_title": strip_quotes(raw.get("text_raw")),
        "category": None,
        "price": None,
        "rating": None,
        "author": clean_text(raw.get("author_raw")),
        "tags": clean_tags(raw.get("tags_raw")),
        "description": None,
        "availability": None,
        "scraped_at": scraped_at,
    }
