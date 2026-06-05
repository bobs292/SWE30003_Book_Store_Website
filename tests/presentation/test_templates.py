"""
Integration tests for HTML template rendering.

These tests verify what users actually see in their browser — page content,
navigation state, form fields, and flash messages. They work by creating a
minimal Flask app that registers real templates and stub blueprints for every
url_for call base.html makes, then checking the rendered HTML.
"""

import os

import pytest
from flask import Blueprint, Flask, render_template, session

TEMPLATE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../src/presentation/templates")
)

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

CART_ITEMS = [
    {
        "book": {
            "id": 1,
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "price": 19.99,
            "stock": 5,
        },
        "quantity": 2,
        "line_total": 39.98,
    }
]


class _StubCustomer:
    def __init__(self, customer_id, email):
        self.customer_id = customer_id
        self.email = email


class _StubCustomerRepo:
    def __init__(self):
        self._store = {}

    def seed(self, customer_id, email):
        self._store[customer_id] = _StubCustomer(customer_id, email)

    def find_by_id(self, customer_id):
        return self._store.get(customer_id)


@pytest.fixture
def stub_repo():
    return _StubCustomerRepo()


@pytest.fixture
def app(stub_repo):
    flask_app = Flask(__name__, template_folder=TEMPLATE_DIR)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test"

    # ------------------------------------------------------------------ #
    # All endpoints base.html references via url_for.                      #
    # ------------------------------------------------------------------ #

    @flask_app.route("/")
    def homepage():
        return render_template("home.html")

    auth_bp = Blueprint("auth", __name__)

    @auth_bp.route("/register")
    def register():
        return render_template("register.html")

    @auth_bp.route("/login")
    def login():
        return render_template("login.html")

    @auth_bp.route("/logout")
    def logout():
        session.clear()
        return ""

    flask_app.register_blueprint(auth_bp)

    catalogue_bp = Blueprint("catalogue", __name__)

    @catalogue_bp.route("/catalogue")
    def catalogue_page():
        return render_template("catalogue.html", books=BOOKS)

    flask_app.register_blueprint(catalogue_bp)

    order_bp = Blueprint("order", __name__)

    @order_bp.route("/cart")
    def cart():
        return render_template("cart.html", cart_items=[], subtotal=0.0)

    @order_bp.route("/cart/with-items")
    def cart_with_items():
        return render_template("cart.html", cart_items=CART_ITEMS, subtotal=39.98)

    @order_bp.route("/cart/add", methods=["POST"])
    def cart_add():
        return ""

    @order_bp.route("/cart/update", methods=["POST"])
    def cart_update():
        return ""

    @order_bp.route("/cart/remove", methods=["POST"])
    def cart_remove():
        return ""

    @order_bp.route("/cart/clear", methods=["POST"])
    def cart_clear():
        return ""

    @order_bp.route("/checkout")
    def checkout():
        return ""

    flask_app.register_blueprint(order_bp)

    # ------------------------------------------------------------------ #
    # Context processors (mirrors app.py behaviour).                       #
    # ------------------------------------------------------------------ #

    @flask_app.context_processor
    def inject_cart_count():
        cart = session.get("cart")
        if not isinstance(cart, dict):
            return {"cart_count": 0}
        total = 0
        for value in cart.values():
            try:
                total += int(value)
            except (TypeError, ValueError):
                continue
        return {"cart_count": total}

    @flask_app.context_processor
    def inject_user_email():
        customer_id = session.get("customer_id")
        if not customer_id:
            return {}
        customer = stub_repo.find_by_id(customer_id)
        if customer:
            return {"current_user_email": customer.email}
        return {}

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ============================================================================
# Navigation — authentication state
# base.html shows Register/Login when logged out and Logout when logged in.


def test_nav_shows_register_when_logged_out(client):
    response = client.get("/")
    assert b"Register" in response.data


def test_nav_shows_login_when_logged_out(client):
    response = client.get("/")
    assert b"Login" in response.data


def test_nav_hides_logout_when_logged_out(client):
    response = client.get("/")
    assert b"Logout" not in response.data


def test_nav_shows_logout_when_logged_in(client, stub_repo):
    stub_repo.seed(1, "jane@example.com")
    with client.session_transaction() as sess:
        sess["customer_id"] = 1
    response = client.get("/")
    assert b"Logout" in response.data


def test_nav_hides_register_when_logged_in(client, stub_repo):
    stub_repo.seed(1, "jane@example.com")
    with client.session_transaction() as sess:
        sess["customer_id"] = 1
    response = client.get("/")
    # The nav Register link must be absent; the word may still appear in
    # page headings so we check for the nav href instead.
    assert b'href="/register"' not in response.data


def test_nav_shows_user_email_when_logged_in(client, stub_repo):
    stub_repo.seed(1, "jane@example.com")
    with client.session_transaction() as sess:
        sess["customer_id"] = 1
    response = client.get("/")
    assert b"jane@example.com" in response.data


# ============================================================================
# Navigation — cart count badge
# The cart icon in base.html shows a badge with the total number of items.


def test_cart_count_badge_hidden_with_empty_cart(client):
    # The badge is only rendered when cart_count > 0, so an empty cart must
    # produce no cart-count element.
    response = client.get("/")
    assert b'class="cart-count"' not in response.data


def test_cart_count_badge_shows_total_items(client):
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 3, "2": 2}
    response = client.get("/")
    assert b'class="cart-count">5<' in response.data


def test_cart_count_badge_hidden_with_corrupted_cart(client):
    # A non-dict cart value must be treated as empty — no badge rendered.
    with client.session_transaction() as sess:
        sess["cart"] = "corrupted"
    response = client.get("/")
    assert b'class="cart-count"' not in response.data


# ============================================================================
# Register page — form fields
# The register form must expose every field the service expects.


def test_register_page_returns_200(client):
    assert client.get("/register").status_code == 200


def test_register_has_first_name_field(client):
    assert b'name="first_name"' in client.get("/register").data


def test_register_has_last_name_field(client):
    assert b'name="last_name"' in client.get("/register").data


def test_register_has_email_field(client):
    assert b'name="email"' in client.get("/register").data


def test_register_has_password_field(client):
    assert b'name="password"' in client.get("/register").data


def test_register_has_phone_number_field(client):
    assert b'name="phone_number"' in client.get("/register").data


def test_register_has_street_field(client):
    assert b'name="street"' in client.get("/register").data


def test_register_has_suburb_field(client):
    assert b'name="suburb"' in client.get("/register").data


def test_register_has_state_field(client):
    assert b'name="state"' in client.get("/register").data


def test_register_has_postcode_field(client):
    assert b'name="postcode"' in client.get("/register").data


# ============================================================================
# Login page — form fields


def test_login_page_returns_200(client):
    assert client.get("/login").status_code == 200


def test_login_has_email_field(client):
    assert b'name="email"' in client.get("/login").data


def test_login_has_password_field(client):
    assert b'name="password"' in client.get("/login").data


# ============================================================================
# Flash messages
# Flash messages are rendered with a CSS class matching their category so the
# stylesheet can colour them correctly.


def test_flash_error_has_error_class(app, client):
    with client.session_transaction() as sess:
        sess["_flashes"] = [("error", "Something went wrong.")]
    response = client.get("/register")
    assert b'class="flash error"' in response.data
    assert b"Something went wrong." in response.data


def test_flash_success_has_success_class(app, client):
    with client.session_transaction() as sess:
        sess["_flashes"] = [("success", "All good!")]
    response = client.get("/register")
    assert b'class="flash success"' in response.data
    assert b"All good!" in response.data


# ============================================================================
# Catalogue page


def test_catalogue_page_returns_200(client):
    assert client.get("/catalogue").status_code == 200


def test_catalogue_shows_book_titles(client):
    response = client.get("/catalogue")
    assert b"The Hobbit" in response.data
    assert b"Dune" in response.data


def test_catalogue_shows_in_stock_add_to_cart(client):
    response = client.get("/catalogue")
    assert b"Add to cart" in response.data


def test_catalogue_shows_out_of_stock_label(client):
    response = client.get("/catalogue")
    assert b"Out of stock" in response.data


# ============================================================================
# Cart page — empty and with items


def test_cart_empty_returns_200(client):
    assert client.get("/cart").status_code == 200


def test_cart_empty_shows_empty_message(client):
    response = client.get("/cart")
    assert b"Your cart is empty" in response.data


def test_cart_with_items_returns_200(client):
    assert client.get("/cart/with-items").status_code == 200


def test_cart_with_items_shows_book_title(client):
    response = client.get("/cart/with-items")
    assert b"The Hobbit" in response.data


def test_cart_with_items_shows_quantity(client):
    response = client.get("/cart/with-items")
    # The quantity input must carry the current quantity as its value.
    assert b'value="2"' in response.data


def test_cart_with_items_shows_subtotal(client):
    response = client.get("/cart/with-items")
    assert b"39.98" in response.data


def test_cart_with_items_shows_proceed_to_checkout(client):
    response = client.get("/cart/with-items")
    assert b"Proceed to checkout" in response.data
