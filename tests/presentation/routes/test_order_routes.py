import pytest
from flask import Blueprint, Flask

from src.domain.gateways.address_gateway import AddressGateway
from src.domain.models.book_title import Book
from src.presentation.routes.order_routes import create_order_routes

# ============================================================================
# Test data
# These are the fake books used across all tests.
# Book id 1 (The Hobbit) has 5 copies in stock and can be added to the cart.
# Book id 2 (Dune) has 0 copies in stock and cannot be added to the cart.
# Tests that need to check out-of-stock behaviour use book id 2.

BOOKS = [
    Book(id="1", title="The Hobbit", price=19.99, stock=5),
    Book(id="2", title="Dune", price=24.99, stock=0),
]


# ============================================================================
# Fake service
# The real catalogue service reads books from a database.
# In tests we do not want to set up a database just to check cart logic,
# so we replace it with a fake version that always returns the BOOKS list
# above. This is called a "fake" or "stub": a simplified stand-in for a real
# object that behaves the same way the route expects, but does nothing
# complicated.


class FakeCatalogueService:
    def list_books(self):
        # Returns the fixed BOOKS list above instead of querying the database.
        return BOOKS


class FakeCheckoutService:
    def process_checkout(self, *args, **kwargs):
        return None, None


class FakeCustomerRepo:
    def find_by_id(self, customer_id):
        return None


class FakeAddressGateway(AddressGateway):
    def validate(self, street, suburb, state, postcode):
        return None


# ============================================================================
# Fixtures
# A pytest fixture is a function that sets something up before a test runs.
# Any test that lists a fixture name as a parameter will automatically
# receive the value that fixture returns.


@pytest.fixture
def app():
    # Creates a minimal Flask application for testing.
    # We register two blueprints:
    #   - A stub catalogue blueprint so that when cart_add tries to redirect
    #     back to the catalogue page, Flask can find the route. Without this,
    #     Flask would raise an error because it does not know what
    #     'catalogue.catalogue_page' refers to.
    #   - The real order blueprint wired up with our fake catalogue service.
    # A blueprint in Flask is a way of grouping related routes together.
    app = Flask(__name__, template_folder="../../../src/presentation/templates")
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test"

    catalogue_bp = Blueprint("catalogue", __name__)

    @catalogue_bp.route("/catalogue")
    def catalogue_page():
        # Empty response. This stub exists only so Flask can resolve
        # url_for('catalogue.catalogue_page') without raising an error.
        return ""

    app.register_blueprint(catalogue_bp)

    # Stub routes for every url_for call made by base.html.
    # base.html is the shared template that all pages extend, so loading
    # any full page in a test requires all of these routes to exist.
    # Each one returns an empty string because the test only cares about
    # the cart logic, not the content of other pages.

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

    order_bp = create_order_routes(
        FakeCatalogueService(),
        FakeCheckoutService(),
        FakeCustomerRepo(),
        FakeAddressGateway(),
    )
    app.register_blueprint(order_bp)
    return app


@pytest.fixture
def client(app):
    # A test client lets us send HTTP requests to the app in tests without
    # running a real web server. It behaves like a browser making requests.
    return app.test_client()


def get_flashes(client):
    # Flash messages in Flask are stored in the session between requests.
    # The session is a small dictionary that Flask keeps on the browser
    # side, signed so it cannot be tampered with.
    # Rather than following the redirect and parsing HTML to find flash
    # messages, we read them directly from the session here. This is
    # simpler and faster.
    with client.session_transaction() as sess:
        return sess.get("_flashes", [])


# ============================================================================
# cart_add
# Tests for POST /cart/add.
# A POST request means the browser is sending data to the server, in this
# case a form submission containing the book id and quantity.
# Valid adds should flash a success message and update the cart stored in
# the session.
# Invalid input such as zero quantity, out-of-stock books, or unknown book
# ids should not modify the cart or show a success message.


def test_cart_add_zero_quantity_flashes_warning(client):
    # If a user submits quantity 0, the route should warn them rather than
    # silently doing nothing.
    client.post("/cart/add", data={"book_id": "1", "quantity": "0"})
    flashes = get_flashes(client)
    assert any(category == "warning" for category, _ in flashes)


def test_cart_add_valid_flashes_success(client):
    # Adding a book with a valid quantity should confirm the action to the
    # user with a success flash message.
    client.post("/cart/add", data={"book_id": "1", "quantity": "2"})
    flashes = get_flashes(client)
    assert any(category == "success" for category, _ in flashes)


def test_cart_add_valid_message_contains_title(client):
    # The success message should name the book so the user knows exactly
    # what was added to their cart.
    client.post("/cart/add", data={"book_id": "1", "quantity": "2"})
    flashes = get_flashes(client)
    assert any("The Hobbit" in msg for _, msg in flashes)


def test_cart_add_out_of_stock_no_flash(client):
    # If a book has no stock, the route should silently redirect without
    # showing any flash message. The catalogue page itself handles showing
    # the out-of-stock state to the user.
    client.post("/cart/add", data={"book_id": "2", "quantity": "1"})
    flashes = get_flashes(client)
    assert flashes == []


def test_cart_add_invalid_book_id_no_flash(client):
    # A book id that does not exist in the catalogue should be silently
    # rejected. There is nothing useful to tell the user in this case as
    # it should not happen through normal use of the site.
    client.post("/cart/add", data={"book_id": "999", "quantity": "1"})
    flashes = get_flashes(client)
    assert flashes == []


def test_cart_add_capped_at_stock(client):
    # If a user requests more copies than are available, the quantity added
    # should be capped at the stock level. Book id 1 has 5 in stock, so
    # requesting 100 should result in 5 being added.
    client.post("/cart/add", data={"book_id": "1", "quantity": "100"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert cart.get("1") == 5


def test_cart_add_accumulates_quantity_on_second_add(client):
    # Adding the same book twice should add the quantities together, not
    # replace the first quantity with the second. If 2 copies are already
    # in the cart and 2 more are added, the cart should show 4.
    client.post("/cart/add", data={"book_id": "1", "quantity": "2"})
    client.post("/cart/add", data={"book_id": "1", "quantity": "2"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert cart.get("1") == 4


def test_cart_add_negative_quantity_no_success_flash(client):
    # A negative quantity submitted via the form should be treated the
    # same as zero and not add anything to the cart. This guards against
    # a user or a browser manually sending a negative number in the form
    # data.
    client.post("/cart/add", data={"book_id": "1", "quantity": "-1"})
    flashes = get_flashes(client)
    assert not any(category == "success" for category, _ in flashes)


# ============================================================================
# cart_update
# Tests for POST /cart/update.
# The cart page lets users change the quantity of a book already in their
# cart. Changing to a new quantity should flash success.
# Submitting the same quantity that is already in the cart should flash a
# warning so the user knows their change had no effect.
# Setting quantity to 0 or below should remove the item from the cart.


def test_cart_update_quantity_unchanged_flashes_warning(client):
    # If the user submits a quantity that matches what is already in the
    # cart, warn them so they know nothing changed.
    # session_transaction() lets us directly set session data before making
    # a request, which is how we put a book in the cart before testing the
    # update.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "2"})
    flashes = get_flashes(client)
    assert any(category == "warning" for category, _ in flashes)


def test_cart_update_quantity_changed_flashes_success(client):
    # Changing to a different valid quantity should confirm the update to
    # the user.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "3"})
    flashes = get_flashes(client)
    assert any(category == "success" for category, _ in flashes)


def test_cart_update_quantity_changed_message_contains_title(client):
    # The success message should name the book so the user knows which
    # item was updated.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "3"})
    flashes = get_flashes(client)
    assert any("The Hobbit" in msg for _, msg in flashes)


def test_cart_update_zero_quantity_removes_item(client):
    # Setting quantity to 0 is how a user removes an item via the update
    # form. The book should no longer appear in the cart after this.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "0"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert "1" not in cart


def test_cart_update_zero_quantity_flashes_success(client):
    # Removing an item via the update form should confirm the removal with
    # a success message, not an error.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "0"})
    flashes = get_flashes(client)
    assert any(category == "success" for category, _ in flashes)


def test_cart_update_book_not_in_cart_no_flash(client):
    # If the book being updated is not in the cart at all, the route
    # should silently redirect without showing any flash message.
    with client.session_transaction() as sess:
        sess["cart"] = {}
    client.post("/cart/update", data={"book_id": "1", "quantity": "2"})
    flashes = get_flashes(client)
    assert flashes == []


def test_cart_update_capped_at_stock(client):
    # Updating to a quantity higher than available stock should cap at
    # the stock level, the same way cart_add does. Book id 1 has 5 in
    # stock, so updating to 100 should result in 5 being stored.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "100"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert cart.get("1") == 5


def test_cart_update_negative_quantity_removes_item(client):
    # A negative quantity should be treated the same as zero and remove
    # the item from the cart. This covers a user or browser manually
    # sending a negative number in the form data.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/update", data={"book_id": "1", "quantity": "-1"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert "1" not in cart


# ============================================================================
# cart_remove
# Tests for POST /cart/remove.
# The remove button on the cart page sends a POST request with just the
# book id. Removing an item should flash a success message that names
# the book. Attempting to remove a book that is not in the cart should
# produce no flash.


def test_cart_remove_flashes_success(client):
    # Removing a book that is in the cart should flash a success message
    # so the user knows the removal worked.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/remove", data={"book_id": "1"})
    flashes = get_flashes(client)
    assert any(category == "success" for category, _ in flashes)


def test_cart_remove_message_contains_title(client):
    # The flash message should name the book that was removed so the user
    # gets clear confirmation of what happened.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/remove", data={"book_id": "1"})
    flashes = get_flashes(client)
    assert any("The Hobbit" in msg for _, msg in flashes)


def test_cart_remove_item_no_longer_in_cart(client):
    # After a successful remove the book should not appear in the
    # session cart.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/remove", data={"book_id": "1"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert "1" not in cart


def test_cart_remove_book_not_in_cart_no_flash(client):
    # If the book is not in the cart, the route should silently redirect.
    with client.session_transaction() as sess:
        sess["cart"] = {}
    client.post("/cart/remove", data={"book_id": "1"})
    flashes = get_flashes(client)
    assert flashes == []


def test_cart_remove_leaves_other_books_untouched(client):
    # Removing one book from a cart that contains multiple books should
    # only remove the requested book. The other books should still be
    # there.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2, "2": 1}
    client.post("/cart/remove", data={"book_id": "1"})
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert "1" not in cart
    assert "2" in cart


# ============================================================================
# cart_clear
# Tests for POST /cart/clear.
# The clear button removes everything from the cart in one action.
# Clearing a non-empty cart should flash a success message that tells the
# user how many items were removed.
# Clearing an already empty cart should produce no flash because there is
# nothing to report.


def test_cart_clear_flashes_success_with_item_count(client):
    # The flash message should tell the user how many items were cleared
    # so they know the action had the expected effect.
    # Cart stores quantities so {'1': 3} means 3 copies of book id 1.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 3}
    client.post("/cart/clear")
    flashes = get_flashes(client)
    assert any(category == "success" for category, _ in flashes)
    assert any("3" in msg for _, msg in flashes)


def test_cart_clear_empties_cart(client):
    # After clearing, the cart in the session should be an empty
    # dictionary.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2}
    client.post("/cart/clear")
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert cart == {}


def test_cart_clear_empty_cart_no_flash(client):
    # If the cart is already empty there is nothing to report, so no
    # flash message should appear.
    with client.session_transaction() as sess:
        sess["cart"] = {}
    client.post("/cart/clear")
    flashes = get_flashes(client)
    assert flashes == []


def test_cart_clear_multiple_different_books(client):
    # Clearing a cart with multiple different books should remove all of
    # them, not just the first one. This test uses two different book ids
    # to confirm.
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2, "2": 1}
    client.post("/cart/clear")
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert cart == {}


# ============================================================================
# _build_cart_items edge cases
# _build_cart_items is the helper that builds the list of items to display
# on the cart page. It is called inside the cart route, not directly from
# a URL, so we test it by loading the cart page and checking what comes
# back.


def test_cart_page_drops_book_removed_from_catalogue(client):
    # If a book is in the session cart but has since been removed from
    # the catalogue, the cart page should silently drop it rather than
    # crashing. This simulates a book being deleted by an admin while a
    # customer has it sitting in their cart.
    # Book id 99 does not exist in the BOOKS list used by
    # FakeCatalogueService.
    with client.session_transaction() as sess:
        sess["cart"] = {"99": 1}
    response = client.get("/cart")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        cart = sess.get("cart", {})
    assert "99" not in cart


# ============================================================================
# checkout
# Tests for /checkout route.
# When unauthenticated, a user trying to access checkout should be
# redirected to login with a flag that indicates they came from checkout.
# This flag should then cause the login route to redirect back to checkout
# instead of to the homepage.


def test_checkout_get_unauthenticated_redirects_to_login(client):
    # An unauthenticated user accessing /checkout should be redirected to
    # the login page.
    response = client.get("/checkout")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_checkout_get_unauthenticated_sets_checkout_flag_in_session(client):
    # When redirecting to login, the route should set a flag in the session
    # so the login route knows this came from a checkout attempt.
    client.get("/checkout")
    with client.session_transaction() as sess:
        assert sess.get("checkout_login_message") is True
