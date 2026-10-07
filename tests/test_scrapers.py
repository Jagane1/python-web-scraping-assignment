from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from tests.conftest_helpers import FakeSession, book_page, fake_site, quote_page


def test_books_pagination_follows_next_links_and_fetches_details():
    session = FakeSession(fake_site())
    scraper = BooksScraper(session=session, delay=0)
    records = scraper.scrape()
    assert [r["title"] for r in records] == ["A Light in the Attic", "Tipping the Velvet", "Soumission"]
    assert records[0]["category_raw"] == "Poetry"
    assert records[0]["url"] == "https://books.toscrape.com/catalogue/a-light_1/index.html"
    assert records[2]["url"] == "https://books.toscrape.com/catalogue/soumission_3/index.html"  # relative to page-2
    assert records[1]["description_raw"] is None                     # missing element -> None, no crash
    assert scraper.stats["pages_scraped"] == 2


def test_books_skip_details_makes_no_detail_requests():
    session = FakeSession(fake_site())
    BooksScraper(session=session, delay=0, fetch_details=False).scrape()
    assert len(session.requested) == 2                               # just the two listing pages


def test_quotes_pagination_and_missing_tags():
    scraper = QuotesScraper(session=FakeSession(fake_site()), delay=0)
    records = scraper.scrape()
    assert len(records) == 3
    assert records[1]["tags_raw"] == []
    assert records[2]["page_url"] == "https://quotes.toscrape.com/page/2/"


def test_failed_page_is_logged_and_stops_source_without_raising():
    pages = fake_site()
    pages["https://quotes.toscrape.com/page/2/"] = None             # connection error
    scraper = QuotesScraper(session=FakeSession(pages), delay=0)
    records = scraper.scrape()
    assert len(records) == 2 and scraper.stats["pages_failed"] == 1


def test_http_404_is_handled():
    pages = {"https://quotes.toscrape.com/": quote_page([], "/page/2/")}  # page 2 -> 404
    scraper = QuotesScraper(session=FakeSession(pages), delay=0)
    assert scraper.scrape() == [] and scraper.stats["pages_failed"] == 1


def test_detail_failure_keeps_the_book():
    pages = fake_site()
    pages["https://books.toscrape.com/catalogue/a-light_1/index.html"] = None
    scraper = BooksScraper(session=FakeSession(pages), delay=0)
    records = scraper.scrape()
    assert len(records) == 3 and records[0]["category_raw"] is None
    assert scraper.stats["detail_failures"] == 1


def test_looping_next_link_does_not_hang():
    url = "https://quotes.toscrape.com/"
    scraper = QuotesScraper(session=FakeSession({url: quote_page([], "/")}), delay=0)
    scraper.scrape()
    assert scraper.stats["pages_scraped"] == 1


def test_one_broken_record_does_not_lose_the_page():
    html = book_page([book_ok(), '<article class="product_pod"><h3><a title="X"></a></h3></article>'])
    scraper = BooksScraper(session=FakeSession({"https://books.toscrape.com/": html}), delay=0, fetch_details=False)
    assert len(scraper.scrape()) == 2                                # missing price/rating/href -> None fields


def book_ok():
    from tests.conftest_helpers import book
    return book("Ok", "ok/index.html")
