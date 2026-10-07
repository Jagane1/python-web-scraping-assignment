from processing.cleaning import (
    clean_price, clean_rating, clean_tags, clean_text, normalize_url, strip_quotes,
)


def test_clean_text_collapses_whitespace():
    assert clean_text("  Hello \n\t World\xa0! ") == "Hello World !"


def test_clean_text_empty_becomes_none():
    assert clean_text("   \n ") is None
    assert clean_text(None) is None


def test_strip_quotes_removes_curly_quotes():
    assert strip_quotes("\u201cThe world.\u201d") == "The world."
    assert strip_quotes('  "plain"  ') == "plain"
    assert strip_quotes("\u201c\u201d") is None


def test_clean_price():
    assert clean_price("£51.77") == 51.77
    assert clean_price("Â£51.77") == 51.77          # mis-decoded pound sign still works
    assert clean_price("£1,234.50") == 1234.5
    assert clean_price("free") is None
    assert clean_price(None) is None


def test_clean_rating():
    assert clean_rating("star-rating Three") == 3
    assert clean_rating("star-rating Five") == 5
    assert clean_rating("star-rating") is None
    assert clean_rating(None) is None


def test_clean_tags_lowercase_unique_sorted():
    assert clean_tags(["Love", " life ", "love"]) == "life;love"
    assert clean_tags([]) is None
    assert clean_tags(None) is None


def test_normalize_url():
    assert normalize_url("a/b.html", "https://x.com/c/") == "https://x.com/c/a/b.html"
    assert normalize_url("  https://x.com/a ") == "https://x.com/a"
    assert normalize_url("ftp://x.com/a") is None
    assert normalize_url("not a url") is None
    assert normalize_url(None) is None
