"""Fingerprint-based duplicate detection.

Identity rules (documented in the README):
  Books : source + title + price
  Quotes: source + author + first 50 characters of the quote text
Each part is lowercased, stripped of punctuation and whitespace-collapsed
*before* hashing, so spacing / capitalisation / punctuation differences vanish.
Note: the real site has two different books with the same title at £46.02 and £32.30.
"""
from __future__ import annotations

import hashlib
import re

import config


def _norm(value: str | None) -> str:
    text = re.sub(r"[^\w\s]", "", (value or "").lower())
    return " ".join(text.split())


def make_fingerprint(rec: dict) -> str:
    source = _norm(rec.get("source"))
    if rec.get("source") == config.QUOTES_SOURCE:
        # truncate AFTER normalising so leading spaces/quotes cannot shift the cut
        text = _norm(rec.get("name_or_title"))[: config.QUOTE_FINGERPRINT_CHARS]
        key = f"{source}|{_norm(rec.get('author'))}|{text}"
    else:
        price = rec.get("price")
        price_key = f"{price:.2f}" if isinstance(price, (int, float)) and not isinstance(price, bool) else ""
        key = f"{source}|{_norm(rec.get('name_or_title'))}|{price_key}"
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def find_duplicates(records: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (unique, duplicates). The first occurrence is kept."""
    seen: set[str] = set()
    unique: list[dict] = []
    dupes: list[dict] = []
    for rec in records:
        fp = make_fingerprint(rec)
        if fp in seen:
            dupes.append(rec)
        else:
            seen.add(fp)
            unique.append(rec)
    return unique, dupes
