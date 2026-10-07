"""Small, pure cleaning functions: a value goes in, a cleaned value comes out.

No internet and no file access here, so everything can be tested with plain strings.
Convention: "nothing usable" is always returned as None.
"""
from __future__ import annotations

import re
from typing import Iterable
from urllib.parse import urljoin, urlparse

RATING_MAP = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
_QUOTE_CHARS = "\u201c\u201d\u2018\u2019\"'"   # curly and straight quotes


def clean_text(value: str | None) -> str | None:
    """Collapse tabs/newlines/non-breaking spaces into single spaces and trim."""
    if value is None:
        return None
    text = " ".join(str(value).replace("\xa0", " ").split())
    return text or None


def strip_quotes(value: str | None) -> str | None:
    """Remove the quotation marks wrapped around quote text."""
    text = clean_text(value)
    if text is None:
        return None
    text = text.strip(_QUOTE_CHARS).strip()
    return text or None


def clean_price(raw: str | None) -> float | None:
    """'£51.77' -> 51.77. Returns None when no number is found."""
    if not raw:
        return None
    match = re.search(r"\d+(?:\.\d+)?", str(raw).replace(",", ""))
    return float(match.group()) if match else None


def clean_rating(raw: str | None) -> int | None:
    """'star-rating Three' -> 3. Returns None when no rating word is found."""
    for word in (raw or "").lower().split():
        if word in RATING_MAP:
            return RATING_MAP[word]
    return None


def clean_tags(tags: Iterable[str] | None) -> str | None:
    """['Love', 'life', 'love'] -> 'life;love' (lowercase, unique, sorted)."""
    if not tags:
        return None
    cleaned = {t.lower() for t in (clean_text(tag) for tag in tags) if t}   # lowercase BEFORE de-duplicating
    return ";".join(sorted(cleaned)) or None


def normalize_url(url: str | None, base: str | None = None) -> str | None:
    """Make a URL absolute. Returns None if the result is not http(s) with a host."""
    url = clean_text(url)
    if not url:
        return None
    full = urljoin(base, url) if base else url
    parsed = urlparse(full)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return full
