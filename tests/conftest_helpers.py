"""Offline fake website + fake session shared by the scraper/pipeline tests."""
import requests


class FakeResponse:
    def __init__(self, text="", status=200):
        self.text, self.status_code, self.encoding = text, status, None

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")


class FakeSession:
    """Maps URL -> HTML. A value of None simulates a connection failure; missing URL = 404."""
    def __init__(self, pages):
        self.pages, self.requested = pages, []

    def get(self, url, timeout=None):
        self.requested.append(url)
        if url not in self.pages:
            return FakeResponse("not found", 404)
        if self.pages[url] is None:
            raise requests.ConnectionError("boom")
        return FakeResponse(self.pages[url])


def book(title, href, price="£51.77", rating="Three"):
    return f'''<article class="product_pod"><p class="star-rating {rating}"></p>
    <h3><a href="{href}" title="{title}">{title[:10]}...</a></h3>
    <div class="product_price"><p class="price_color">{price}</p>
    <p class="instock availability"> In stock </p></div></article>'''


def book_page(books, next_href=None):
    nxt = f'<li class="next"><a href="{next_href}">next</a></li>' if next_href else ""
    return f"<html><body>{''.join(books)}<ul class='pager'>{nxt}</ul></body></html>"


def book_detail(category, description):
    desc = f'<div id="product_description"><h2>Product Description</h2></div><p>{description}</p>' if description else ""
    return f'''<html><body><ul class="breadcrumb"><li><a href="/">Home</a></li>
    <li><a href="/books">Books</a></li><li><a href="/c">{category}</a></li><li>Title</li></ul>
    <p class="instock availability">In stock (22 available)</p>{desc}</body></html>'''


def quote(text, author, tags=()):
    t = "".join(f'<a class="tag" href="/tag/{x}/">{x}</a>' for x in tags)
    return f'''<div class="quote"><span class="text">\u201c{text}\u201d</span>
    <span>by <small class="author">{author}</small><a href="/author/x">(about)</a></span>
    <div class="tags">Tags: {t}</div></div>'''


def quote_page(quotes, next_href=None):
    nxt = f'<li class="next"><a href="{next_href}">Next</a></li>' if next_href else ""
    return f"<html><body>{''.join(quotes)}<ul class='pager'>{nxt}</ul></body></html>"


def fake_site():
    b = "https://books.toscrape.com/"
    q = "https://quotes.toscrape.com/"
    return {
        b: book_page([book("A Light in the Attic", "catalogue/a-light_1/index.html"),
                      book("Tipping the Velvet", "catalogue/tipping_2/index.html", "£53.74", "One")],
                     "catalogue/page-2.html"),
        b + "catalogue/page-2.html": book_page([book("Soumission", "soumission_3/index.html", "£50.10", "Four")]),
        b + "catalogue/a-light_1/index.html": book_detail("Poetry", "Great   poems\xa0here"),
        b + "catalogue/tipping_2/index.html": book_detail("Historical Fiction", None),
        b + "catalogue/soumission_3/index.html": book_detail("Fiction", "France, 2022."),
        q: quote_page([quote("The world as we have created it", "Albert Einstein", ["change", "World"]),
                       quote("It is our choices", "J.K. Rowling")], "/page/2/"),
        q + "page/2/": quote_page([quote("The world as we have created it", "  albert einstein ", ["change"])]),
    }
