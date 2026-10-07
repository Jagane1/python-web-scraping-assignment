from processing.validation import validate_record


def good_book():
    return {"source": "Books to Scrape", "source_url": "https://books.toscrape.com/x",
            "name_or_title": "T", "price": 10.0, "rating": 3, "author": None}


def good_quote():
    return {"source": "Quotes to Scrape", "source_url": "https://quotes.toscrape.com/",
            "name_or_title": "Q", "price": None, "rating": None, "author": "Someone"}


def test_valid_records_have_no_problems():
    assert validate_record(good_book()) == []
    assert validate_record(good_quote()) == []


def test_each_rule_reports_its_reason():
    assert validate_record({**good_book(), "source": "Other"}) == ["unknown_source"]
    assert validate_record({**good_book(), "name_or_title": None}) == ["missing_name"]
    assert validate_record({**good_book(), "source_url": "ftp://x"}) == ["invalid_url"]
    assert validate_record({**good_book(), "source_url": None}) == ["invalid_url"]
    assert validate_record({**good_book(), "price": -1}) == ["invalid_price"]
    assert validate_record({**good_book(), "price": "10"}) == ["invalid_price"]
    assert validate_record({**good_book(), "price": float("nan")}) == ["invalid_price"]
    assert validate_record({**good_book(), "rating": 6}) == ["invalid_rating"]
    assert validate_record({**good_book(), "rating": 0}) == ["invalid_rating"]
    assert validate_record({**good_quote(), "author": None}) == ["missing_author"]


def test_multiple_problems_are_all_reported():
    rec = {**good_book(), "name_or_title": "", "rating": 9}
    assert set(validate_record(rec)) == {"missing_name", "invalid_rating"}


def test_none_price_and_rating_are_allowed():
    assert validate_record({**good_book(), "price": None, "rating": None}) == []
