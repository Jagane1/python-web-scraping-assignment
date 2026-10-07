from processing.deduplication import find_duplicates, make_fingerprint

BOOK = {"source": "Books to Scrape", "author": None}
QUOTE = {"source": "Quotes to Scrape"}


def test_duplicates_ignore_case_and_spaces():
    records = [{**BOOK, "name_or_title": "Example Book Title"},
               {**BOOK, "name_or_title": "  Example Book Title "},
               {**BOOK, "name_or_title": "EXAMPLE BOOK TITLE"}]
    unique, dupes = find_duplicates(records)
    assert len(unique) == 1 and len(dupes) == 2
    assert unique[0]["name_or_title"] == "Example Book Title"      # first occurrence is kept


def test_duplicates_ignore_punctuation():
    a = {**BOOK, "name_or_title": "Hello, World!"}
    b = {**BOOK, "name_or_title": "hello   world"}
    assert make_fingerprint(a) == make_fingerprint(b)


def test_different_books_are_not_duplicates():
    unique, dupes = find_duplicates([{**BOOK, "name_or_title": "A"}, {**BOOK, "name_or_title": "B"}])
    assert len(unique) == 2 and not dupes


def test_quotes_use_author_and_first_50_chars():
    long_text = "x" * 60
    a = {**QUOTE, "author": "Ann", "name_or_title": long_text + " ending one"}
    b = {**QUOTE, "author": " ANN ", "name_or_title": long_text + " different ending"}
    c = {**QUOTE, "author": "Bob", "name_or_title": long_text}
    unique, dupes = find_duplicates([a, b, c])
    assert len(unique) == 2 and len(dupes) == 1                     # a/b match; c has another author


def test_same_text_in_different_sources_is_not_a_duplicate():
    a = {**BOOK, "name_or_title": "Same"}
    b = {**QUOTE, "author": "", "name_or_title": "Same"}
    assert make_fingerprint(a) != make_fingerprint(b)


def test_same_title_different_price_is_not_a_duplicate():
    a = {**BOOK, "name_or_title": "The Star-Touched Queen", "price": 46.02}
    b = {**BOOK, "name_or_title": "The Star-Touched Queen", "price": 32.30}
    unique, dupes = find_duplicates([a, b])
    assert len(unique) == 2 and not dupes


def test_same_title_same_price_with_formatting_noise_is_a_duplicate():
    a = {**BOOK, "name_or_title": "The Star-Touched Queen", "price": 46.02}
    b = {**BOOK, "name_or_title": " THE STAR-TOUCHED  QUEEN ", "price": 46.02}
    unique, dupes = find_duplicates([a, b])
    assert len(unique) == 1 and len(dupes) == 1
