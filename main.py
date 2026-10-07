"""Entry point:  python main.py   (see README for options)."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import config
from pipeline import build_scrapers, run_pipeline


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_dir / "scraper.log", mode="w", encoding="utf-8"),
                  logging.StreamHandler()],
    )


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape Books/Quotes to Scrape into one clean dataset.")
    p.add_argument("--skip-details", action="store_true",
                   help="do not visit each book page (faster; category/description stay empty)")
    p.add_argument("--delay", type=float, default=config.REQUEST_DELAY, help="seconds between requests")
    p.add_argument("--max-pages", type=int, default=None, help="limit pages per source (for quick tests)")
    p.add_argument("--output-dir", type=Path, default=config.OUTPUT_DIR)
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(config.LOG_DIR)
    scrapers = build_scrapers(fetch_details=not args.skip_details, delay=args.delay, max_pages=args.max_pages)
    report = run_pipeline(scrapers, args.output_dir,
                          run_info={"fetch_book_details": not args.skip_details,
                                    "delay_seconds": args.delay, "max_pages": args.max_pages})
    return 0 if report["totals"]["final_record_count"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
