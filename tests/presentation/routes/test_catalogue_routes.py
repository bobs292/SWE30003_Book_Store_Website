from unittest.mock import MagicMock

import pytest
from flask import Blueprint, Flask

from src.presentation.routes.catalogue_routes import create_catalogue_routes

# All fields that catalogue.html references for each book.
BOOKS = [
    {
        "id": 1,
        "title": "The Hobbit",
        "author": "J.R.R. Tolkien",
        "genre": "Fantasy",
        "description": "A hobbit goes on an adventure.",
        "price": 19.99,
        "stock": 5,
        "cover_url": None,
    },
    {
        "id": 2,
        "title": "Dune",
        "author": "Frank Herbert",
        "genre": "Science Fiction",
        "description": "A desert planet epic.",
        "price": 24.99,
        "stock": 0,
        "cover_url": None,
    },
]


class FakeCatalogueService:
    def __init__(self, books=None):
        self._books = BOOKS if books is None else books

    def list_books(self):
        return self._books


def _make_app(catalogue_service):
    app = Flask(__name__, template_folder="../../../src/presentation/templates")
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"

    # Stub routes required by base.html url_for calls.
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


def test_catalogue_calls_list_books():
    mock_service = MagicMock()
    mock_service.list_books.return_value = BOOKS
    app = _make_app(mock_service)
    app.test_client().get("/catalogue")
    mock_service.list_books.assert_called_once()


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
    # The Hobbit has stock > 0 so the add-to-cart form must appear.
    assert b"Add to cart" in response.data


def test_catalogue_out_of_stock_book_shows_out_of_stock(client):
    response = client.get("/catalogue")
    # Dune has stock == 0 so the out-of-stock label must appear.
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
