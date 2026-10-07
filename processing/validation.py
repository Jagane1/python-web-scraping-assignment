"""Check one cleaned record and return the list of problems (empty list = valid)."""
from __future__ import annotations

import config


def validate_record(rec: dict) -> list[str]:
    problems: list[str] = []
    if rec.get("source") not in config.VALID_SOURCES:
        problems.append("unknown_source")
    if not rec.get("name_or_title"):
        problems.append("missing_name")
    if not str(rec.get("source_url") or "").startswith(("http://", "https://")):
        problems.append("invalid_url")

    price = rec.get("price")
    if price is not None:
        # bool is a subclass of int, so exclude it explicitly; price != price catches NaN
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price != price or price < 0:
            problems.append("invalid_price")

    rating = rec.get("rating")
    if rating is not None:
        if isinstance(rating, bool) or not isinstance(rating, int) or not 1 <= rating <= 5:
            problems.append("invalid_rating")

    if rec.get("source") == config.QUOTES_SOURCE and not rec.get("author"):
        problems.append("missing_author")
    return problems
