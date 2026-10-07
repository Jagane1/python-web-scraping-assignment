"""Connects the stages: scrape -> clean -> validate -> deduplicate -> consolidate -> write."""
from __future__ import annotations

import csv
import json
import logging
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import config
from processing.deduplication import find_duplicates
from processing.normalize import normalize_book, normalize_quote
from processing.validation import validate_record
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper

logger = logging.getLogger(__name__)

NORMALIZERS = {config.BOOKS_SOURCE: normalize_book, config.QUOTES_SOURCE: normalize_quote}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def process_source(scraper) -> tuple[list[dict], dict]:
    """Run one source end to end. Never raises: a failure becomes an 'error' in the stats."""
    name = scraper.source_name
    stats = {"collected": 0, "cleaned": 0, "rejected_total": 0, "rejected_by_reason": {},
             "duplicates_detected": 0, "duplicate_examples": [], "final_count": 0, "error": None}
    try:
        raw_records = scraper.scrape()
    except Exception as exc:                                    # last-resort safety net
        logger.exception("[%s] scraper crashed", name)
        raw_records, stats["error"] = [], str(exc)
    stats["collected"] = len(raw_records)

    reasons: Counter = Counter()
    rejected = 0
    valid: list[dict] = []
    normalize = NORMALIZERS[name]
    scraped_at = _now()
    for raw in raw_records:
        try:
            rec = normalize(raw, scraped_at)
        except Exception as exc:                                # unexpected data format
            logger.warning("[%s] cleaning failed (%s): %r", name, exc, raw)
            reasons["normalization_error"] += 1
            rejected += 1
            continue
        stats["cleaned"] += 1
        problems = validate_record(rec)
        if problems:
            logger.warning("[%s] rejected %s: %s", name, problems, rec.get("name_or_title") or rec.get("source_url"))
            reasons.update(problems)
            rejected += 1
        else:
            valid.append(rec)

    unique, dupes = find_duplicates(valid)
    for d in dupes:
        logger.warning("[%s] duplicate removed: %s", name, d["name_or_title"])
    stats.update({
        "rejected_total": rejected,
        "rejected_by_reason": dict(reasons),
        "duplicates_detected": len(dupes),
        "duplicate_examples": [d["name_or_title"] for d in dupes[:5]],
        "final_count": len(unique),
        "scraper_stats": dict(scraper.stats),
    })
    return unique, stats


def write_csv(records: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)                               # None -> empty cell


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def run_pipeline(scrapers: list, output_dir: Path = config.OUTPUT_DIR, run_info: dict | None = None) -> dict:
    start_wall, start = _now(), time.monotonic()
    all_records: list[dict] = []
    per_source: dict[str, dict] = {}
    for scraper in scrapers:                                    # one source failing must not stop the next
        records, stats = process_source(scraper)
        all_records.extend(records)
        per_source[scraper.source_name] = stats

    write_csv(all_records, output_dir / "final_dataset.csv")

    totals = {
        "collected": sum(s["collected"] for s in per_source.values()),
        "cleaned": sum(s["cleaned"] for s in per_source.values()),
        "rejected": sum(s["rejected_total"] for s in per_source.values()),
        "duplicates_detected": sum(s["duplicates_detected"] for s in per_source.values()),
        "final_record_count": len(all_records),
    }
    report = {
        "run": {**(run_info or {}), "started_at": start_wall, "finished_at": _now(),
                "duration_seconds": round(time.monotonic() - start, 1)},
        "sources": per_source,
        "totals": totals,
        # collected - rejected - duplicates must equal the CSV row count
        "counts_reconcile": totals["collected"] - totals["rejected"] - totals["duplicates_detected"]
                            == totals["final_record_count"],
    }
    write_json(report, output_dir / "summary_report.json")
    logger.info("Done: %s", totals)
    return report


def build_scrapers(fetch_details: bool = True, delay: float = config.REQUEST_DELAY,
                   max_pages: int | None = None) -> list:
    return [BooksScraper(delay=delay, max_pages=max_pages, fetch_details=fetch_details),
            QuotesScraper(delay=delay, max_pages=max_pages)]
