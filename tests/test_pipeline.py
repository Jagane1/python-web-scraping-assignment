import csv
import json
import tempfile
from pathlib import Path

from pipeline import run_pipeline
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from tests.conftest_helpers import FakeSession, fake_site


def run(pages, tmp):
    session = FakeSession(pages)
    scrapers = [BooksScraper(session=session, delay=0), QuotesScraper(session=session, delay=0)]
    return run_pipeline(scrapers, Path(tmp))


def test_end_to_end_outputs_and_reconciliation():
    with tempfile.TemporaryDirectory() as tmp:
        report = run(fake_site(), tmp)
        rows = list(csv.DictReader(open(Path(tmp) / "final_dataset.csv", encoding="utf-8")))
        saved = json.load(open(Path(tmp) / "summary_report.json", encoding="utf-8"))

    # 3 books + 3 quotes scraped; the repeated Einstein quote (different spacing/case) is a duplicate
    assert report["totals"]["collected"] == 6
    assert report["sources"]["Quotes to Scrape"]["duplicates_detected"] == 1
    assert len(rows) == 5 == saved["totals"]["final_record_count"]
    assert saved["counts_reconcile"] is True

    book_row = next(r for r in rows if r["name_or_title"] == "A Light in the Attic")
    assert book_row["price"] == "51.77" and book_row["rating"] == "3"
    assert book_row["category"] == "Poetry" and book_row["description"] == "Great poems here"
    assert book_row["author"] == "" and book_row["tags"] == ""

    quote_row = next(r for r in rows if r["author"] == "Albert Einstein")
    assert quote_row["tags"] == "change;world"
    assert not quote_row["name_or_title"].startswith("\u201c")
    assert quote_row["price"] == "" and quote_row["rating"] == ""
    assert {r["source"] for r in rows} == {"Books to Scrape", "Quotes to Scrape"}


def test_one_source_failing_does_not_stop_the_other():
    pages = fake_site()
    pages["https://books.toscrape.com/"] = None                      # books home page unreachable
    with tempfile.TemporaryDirectory() as tmp:
        report = run(pages, tmp)
    assert report["sources"]["Books to Scrape"]["final_count"] == 0
    assert report["sources"]["Quotes to Scrape"]["final_count"] == 2
    assert report["counts_reconcile"] is True


def test_invalid_records_are_rejected_with_reasons():
    pages = fake_site()
    pages["https://quotes.toscrape.com/page/2/"] = pages["https://quotes.toscrape.com/page/2/"].replace(
        "albert einstein", "")                                       # author vanishes -> missing_author
    with tempfile.TemporaryDirectory() as tmp:
        report = run(pages, tmp)
    q = report["sources"]["Quotes to Scrape"]
    assert q["rejected_by_reason"] == {"missing_author": 1} and q["rejected_total"] == 1
    assert report["counts_reconcile"] is True
