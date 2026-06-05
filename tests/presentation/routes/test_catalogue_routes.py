from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.domain.models.book_title import Book
from src.domain.services.search_service import SearchService
from src.presentation.routes.catalogue_routes import create_catalogue_routes

BOOKS = [
    Book(
        id="1",
        title="The Hobbit",
        author="J.R.R. Tolkien",
        genre="Fantasy",
        description="A hobbit goes on an adventure.",
        price=19.99,
        stock=5,
    ),
    Book(
        id="2",
        title="Dune",
        author="Frank Herbert",
        genre="Science Fiction",
        description="A desert planet epic.",
        price=24.99,
        stock=0,
    ),
]


class FakeCatalogueService:
    VALID_SORT_OPTIONS = ["title", "author", "price-low", "price-high"]

    def __init__(self, books=None):
        self._books = BOOKS if books is None else books

    def list_books(self):
        return self._books

    def get_book(self, isbn):
        return next((b for b in self._books if str(b.id) == str(isbn)), None)

    def get_all_genres(self):
        genres = set(book.genre for book in self._books)
        return sorted(genres)

    def filter_by_genre(self, books, genre):
        if not genre or not genre.strip():
            return books
        genre = genre.strip()
        return [b for b in books if b.genre == genre]

    def sort_books(self, books, sort_by="title"):
        sort_by = (sort_by or "title").strip()
        if sort_by == "price-low":
            return sorted(books, key=lambda b: float(b.price))
        elif sort_by == "price-high":
            return sorted(books, key=lambda b: float(b.price), reverse=True)
        elif sort_by == "author":
            return sorted(books, key=lambda b: b.author.lower())
        elif sort_by == "title":
            return sorted(books, key=lambda b: b.title.lower())
        else:
            return books

    def get_valid_sort_options(self):
        return self.VALID_SORT_OPTIONS.copy()

    def browse(self, search_query="", genre="", sort_by="title"):
        books = self.list_books()
        books = SearchService.search_books(books, search_query)
        books = self.filter_by_genre(books, genre)
        books = self.sort_books(books, sort_by)
        return books


def _make_app(catalogue_service):
    app = Flask(__name__, template_folder="../../../src/presentation/templates")
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"

    @app.route("/")
    def homepage():
        return ""

    auth_bp = Blueprint("auth", __name__)

    @auth_bp.route("/register")
    def register():
        return ""

    @auth_bp.route("/login")
    def login():
        return ""

    @auth_bp.route("/logout")
    def logout():
        return ""

    app.register_blueprint(auth_bp)

    order_bp = Blueprint("order", __name__)

    @order_bp.route("/cart")
    def cart():
        return ""

    @order_bp.route("/cart/add", methods=["POST"])
    def cart_add():
        return ""

    app.register_blueprint(order_bp)
    app.register_blueprint(create_catalogue_routes(catalogue_service))
    return app


@pytest.fixture
def app():
    return _make_app(FakeCatalogueService())


@pytest.fixture
def client(app):
    return app.test_client()


# ============================================================================
# GET /catalogue


def test_catalogue_get_returns_200(client):
    response = client.get("/catalogue")
    assert response.status_code == 200


def test_catalogue_calls_browse():
    mock_service = MagicMock()
    mock_service.browse.return_value = BOOKS
    mock_service.get_all_genres.return_value = []
    app = _make_app(mock_service)
    app.test_client().get("/catalogue")
    mock_service.browse.assert_called_once()


def test_catalogue_shows_book_titles(client):
    response = client.get("/catalogue")
    assert b"The Hobbit" in response.data
    assert b"Dune" in response.data


def test_catalogue_shows_book_authors(client):
    response = client.get("/catalogue")
    assert b"J.R.R. Tolkien" in response.data
    assert b"Frank Herbert" in response.data


def test_catalogue_shows_book_prices(client):
    response = client.get("/catalogue")
    assert b"19.99" in response.data
    assert b"24.99" in response.data


def test_catalogue_shows_genre_tags(client):
    response = client.get("/catalogue")
    assert b"Fantasy" in response.data
    assert b"Science Fiction" in response.data


def test_catalogue_in_stock_book_has_add_to_cart_form(client):
    response = client.get("/catalogue")
    assert b"Add to cart" in response.data


def test_catalogue_out_of_stock_book_shows_out_of_stock(client):
    response = client.get("/catalogue")
    assert b"Out of stock" in response.data


def test_catalogue_empty_returns_200():
    app = _make_app(FakeCatalogueService(books=[]))
    response = app.test_client().get("/catalogue")
    assert response.status_code == 200


def test_catalogue_empty_shows_no_books_message():
    app = _make_app(FakeCatalogueService(books=[]))
    response = app.test_client().get("/catalogue")
    assert b"No books are available" in response.data


def test_catalogue_empty_has_no_add_to_cart():
    app = _make_app(FakeCatalogueService(books=[]))
    response = app.test_client().get("/catalogue")
    assert b"Add to cart" not in response.data


def test_catalogue_cards_link_to_detail_page(client):
    response = client.get("/catalogue")
    assert b"/book/" in response.data


# ============================================================================
# Genre filtering


def test_catalogue_shows_genre_filter_menu(client):
    response = client.get("/catalogue")
    assert b"All Books" in response.data
    assert b"Fantasy" in response.data
    assert b"Science Fiction" in response.data


def test_catalogue_filter_by_genre_shows_only_that_genre(client):
    response = client.get("/catalogue?genre=Fantasy")
    assert b"The Hobbit" in response.data
    assert b"Dune" not in response.data


def test_catalogue_filter_by_genre_highlights_active_genre(client):
    response = client.get("/catalogue?genre=Fantasy")
    assert b'class="genre-link active"' in response.data
    assert b"Fantasy" in response.data


def test_catalogue_all_books_link_shows_all_when_no_filter(client):
    response = client.get("/catalogue")
    assert b"All Books" in response.data


# ============================================================================
# Sorting


def test_catalogue_shows_sort_options(client):
    response = client.get("/catalogue")
    assert b'id="sort-select"' in response.data
    assert b"Title (A-Z)" in response.data
    assert b"Price (Low to High)" in response.data


def test_catalogue_default_sort_is_title(client):
    response = client.get("/catalogue")
    assert b"selected" in response.data
    assert b"Title (A-Z)" in response.data


def test_catalogue_sort_by_price_low(client):
    response = client.get("/catalogue?sort=price-low")
    assert response.status_code == 200
    assert b'value="price-low"' in response.data


def test_catalogue_sort_by_price_high(client):
    response = client.get("/catalogue?sort=price-high")
    assert response.status_code == 200


def test_catalogue_sort_by_author(client):
    response = client.get("/catalogue?sort=author")
    assert response.status_code == 200


def test_catalogue_filter_and_sort_together(client):
    response = client.get("/catalogue?genre=Fantasy&sort=price-low")
    assert response.status_code == 200
    assert b"The Hobbit" in response.data
    assert b"Dune" not in response.data


# ============================================================================
# Search


def test_catalogue_shows_search_box(client):
    response = client.get("/catalogue")
    assert b'class="search-input"' in response.data
    assert b"Start typing to search" in response.data


def test_catalogue_search_by_title(client):
    response = client.get("/catalogue?search=Hobbit")
    assert response.status_code == 200
    assert b"The Hobbit" in response.data
    assert b"Dune" not in response.data


def test_catalogue_search_by_author(client):
    response = client.get("/catalogue?search=Frank+Herbert")
    assert response.status_code == 200
    assert b"Dune" in response.data
    assert b"The Hobbit" not in response.data


def test_catalogue_search_case_insensitive(client):
    response = client.get("/catalogue?search=TOLKIEN")
    assert response.status_code == 200
    assert b"The Hobbit" in response.data


def test_catalogue_search_no_results(client):
    response = client.get("/catalogue?search=xyz123nobook")
    assert response.status_code == 200
    assert b"No books are available" in response.data


def test_catalogue_search_with_genre_filter(client):
    response = client.get("/catalogue?search=Fiction&genre=Fantasy")
    assert response.status_code == 200


def test_catalogue_search_preserves_genre_and_sort(client):
    response = client.get("/catalogue?search=Hobbit&genre=Fantasy&sort=price-low")
    assert response.status_code == 200
    assert b"The Hobbit" in response.data


# ============================================================================
# GET /book/<isbn>


def test_book_detail_returns_200(client):
    response = client.get("/book/1")
    assert response.status_code == 200


def test_book_detail_shows_title(client):
    response = client.get("/book/1")
    assert b"The Hobbit" in response.data


def test_book_detail_shows_author(client):
    response = client.get("/book/1")
    assert b"J.R.R. Tolkien" in response.data


def test_book_detail_shows_description(client):
    response = client.get("/book/1")
    assert b"A hobbit goes on an adventure." in response.data


def test_book_detail_shows_price(client):
    response = client.get("/book/1")
    assert b"19.99" in response.data


def test_book_detail_in_stock_shows_add_to_cart(client):
    response = client.get("/book/1")
    assert b"Add to cart" in response.data


def test_book_detail_out_of_stock_shows_label(client):
    response = client.get("/book/2")
    assert b"Out of stock" in response.data


def test_book_detail_unknown_isbn_returns_404(client):
    response = client.get("/book/does-not-exist")
    assert response.status_code == 404


def test_book_detail_calls_get_book():
    mock_service = MagicMock()
    mock_service.get_book.return_value = BOOKS[0]
    mock_service.list_books.return_value = BOOKS
    app = _make_app(mock_service)
    app.test_client().get("/book/9780000000001")
    mock_service.get_book.assert_called_once_with("9780000000001")
