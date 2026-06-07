from unittest.mock import ANY, MagicMock, patch

import pytest
from flask import Blueprint, Flask

from src.presentation.routes.auth_routes import create_auth_routes

# render_template is patched throughout so these tests are decoupled from the
# base template's url_for calls for unrelated blueprints (catalogue, order)
# and from the current_user_email context processor registered in app.py.
# Route logic is the only thing under test here.
_RENDER = "src.presentation.routes.auth_routes.render_template"


@pytest.fixture
def auth_service():
    return MagicMock()


@pytest.fixture
def app(auth_service):
    flask_app = Flask(__name__)
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"

    @flask_app.route("/")
    def homepage():
        return "homepage"

    flask_app.register_blueprint(create_auth_routes(auth_service))

    # Register order blueprint stub so url_for('order.checkout') works
    order_bp = Blueprint("order", __name__)

    @order_bp.route("/checkout")
    def checkout():
        return "checkout"

    flask_app.register_blueprint(order_bp)

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


# ============================================================================
# GET /register


def test_register_get_returns_200(client):
    with patch(_RENDER, return_value="form"):
        response = client.get("/register")
    assert response.status_code == 200


def test_register_get_renders_register_template(client):
    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/register")
    mock_render.assert_called_once_with("register.html", errors={}, form={})


# ============================================================================
# POST /register


def test_register_post_valid_redirects_to_login(client, auth_service):
    auth_service.validate.return_value = {}
    auth_service.register.return_value = None
    response = client.post(
        "/register",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "Passw0rd",
        },
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_register_post_valid_sets_registration_success_flag(client, auth_service):
    # After successful registration, a flag should be set so the login page
    # can display a registration success message.
    auth_service.validate.return_value = {}
    auth_service.register.return_value = None
    client.post(
        "/register",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "Passw0rd",
        },
    )
    with client.session_transaction() as sess:
        assert sess.get("registration_success") is True


def test_register_post_calls_service_with_form_fields(client, auth_service):
    auth_service.validate.return_value = {}
    auth_service.register.return_value = None
    client.post(
        "/register",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "Passw0rd",
            "phone_number": "0412345678",
            "street": "1 Main St",
            "suburb": "Melbourne",
            "state": "VIC",
            "postcode": "3000",
        },
    )
    _, kwargs = auth_service.register.call_args
    assert kwargs["first_name"] == "John"
    assert kwargs["last_name"] == "Smith"
    assert kwargs["email"] == "john@example.com"
    assert kwargs["password"] == "Passw0rd"
    assert kwargs["phone_number"] == "0412345678"
    assert kwargs["street"] == "1 Main St"
    assert kwargs["suburb"] == "Melbourne"
    assert kwargs["state"] == "VIC"
    assert kwargs["postcode"] == "3000"


def test_register_post_empty_phone_passed_as_none(client, auth_service):
    # An empty phone field must be coerced to None so the service sees an
    # absent value rather than an empty string that would fail format checks.
    auth_service.validate.return_value = {}
    auth_service.register.return_value = None
    client.post(
        "/register",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "Passw0rd",
            "phone_number": "",
        },
    )
    _, kwargs = auth_service.register.call_args
    assert kwargs["phone_number"] is None


def test_register_post_empty_address_fields_passed_as_none(client, auth_service):
    # Empty address fields must be coerced to None so the service treats the
    # address as absent rather than triggering validation on blank strings.
    auth_service.validate.return_value = {}
    auth_service.register.return_value = None
    client.post(
        "/register",
        data={
            "first_name": "John",
            "last_name": "Smith",
            "email": "john@example.com",
            "password": "Passw0rd",
            "street": "",
            "suburb": "",
            "state": "",
            "postcode": "",
        },
    )
    _, kwargs = auth_service.register.call_args
    assert kwargs["street"] is None
    assert kwargs["suburb"] is None
    assert kwargs["state"] is None
    assert kwargs["postcode"] is None


def test_register_post_invalid_rerenders_form(client, auth_service):
    # When validate() returns errors the route re-renders the form (200)
    # rather than redirecting so the user can correct their input.
    auth_service.validate.return_value = {"password": "Password must contain..."}
    with patch(_RENDER, return_value="form"):
        response = client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "Smith",
                "email": "john@example.com",
                "password": "bad",
            },
        )
    assert response.status_code == 200


def test_register_post_invalid_renders_register_template(client, auth_service):
    auth_service.validate.return_value = {
        "email": "An account with this email already exists."
    }
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "J",
                "last_name": "S",
                "email": "j@s.co",
                "password": "bad",
            },
        )
    mock_render.assert_called_once_with("register.html", errors=ANY, form=ANY)


def test_register_post_errors_passed_to_template(client, auth_service):
    # The errors dict from validate() must be forwarded to the template so
    # the form can highlight individual fields.
    auth_service.validate.return_value = {
        "email": "An account with this email already exists."
    }
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "J",
                "last_name": "S",
                "email": "j@s.co",
                "password": "bad",
            },
        )
    _, kwargs = mock_render.call_args
    assert "email" in kwargs["errors"]


def test_register_post_missing_first_name_shows_error(client, auth_service):
    # The route checks first_name before calling the service — an empty
    # first_name must produce a field-level error without reaching register().
    auth_service.validate.return_value = {}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "",
                "last_name": "Smith",
                "email": "a@b.co",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert "first_name" in kwargs["errors"]


def test_register_post_missing_last_name_shows_error(client, auth_service):
    auth_service.validate.return_value = {}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "",
                "email": "a@b.co",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert "last_name" in kwargs["errors"]


def test_register_post_whitespace_first_name_shows_error(client, auth_service):
    # Whitespace-only first name must be treated as absent.
    auth_service.validate.return_value = {}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "   ",
                "last_name": "Smith",
                "email": "a@b.co",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert "first_name" in kwargs["errors"]


def test_register_post_whitespace_last_name_shows_error(client, auth_service):
    auth_service.validate.return_value = {}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "   ",
                "email": "a@b.co",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert "last_name" in kwargs["errors"]


def test_register_post_invalid_email_shows_error(client, auth_service):
    # Service returns an email error — route must forward it to the template.
    auth_service.validate.return_value = {"email": "Enter a valid email address."}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "Smith",
                "email": "not-an-email",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert kwargs["errors"]["email"] == "Enter a valid email address."


def test_register_post_invalid_password_shows_error(client, auth_service):
    auth_service.validate.return_value = {"password": "Password must contain..."}
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "Smith",
                "email": "a@b.co",
                "password": "weak",
            },
        )
    _, kwargs = mock_render.call_args
    assert "password" in kwargs["errors"]


def test_register_post_duplicate_email_shows_error(client, auth_service):
    auth_service.validate.return_value = {
        "email": "An account with this email already exists."
    }
    with patch(_RENDER, return_value="form") as mock_render:
        client.post(
            "/register",
            data={
                "first_name": "John",
                "last_name": "Smith",
                "email": "taken@example.com",
                "password": "Passw0rd",
            },
        )
    _, kwargs = mock_render.call_args
    assert "email" in kwargs["errors"]


def test_register_post_missing_first_name_does_not_call_register(client, auth_service):
    # register() must never be called when there are validation errors.
    auth_service.validate.return_value = {}
    with patch(_RENDER, return_value="form"):
        client.post(
            "/register",
            data={
                "first_name": "",
                "last_name": "Smith",
                "email": "a@b.co",
                "password": "Passw0rd",
            },
        )
    auth_service.register.assert_not_called()


# ============================================================================
# GET /login


def test_login_get_returns_200(client):
    with patch(_RENDER, return_value="form"):
        response = client.get("/login")
    assert response.status_code == 200


def test_login_get_renders_login_template(client):
    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/login")
    mock_render.assert_called_once_with(
        "login.html",
        errors={},
        form={},
        checkout_login=False,
        registration_success=False,
    )


# ============================================================================
# POST /login


def test_login_post_valid_redirects_to_homepage(client, auth_service):
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    response = client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_login_post_valid_sets_customer_id_in_session(client, auth_service):
    auth_service.login.return_value = {"customer_id": 42, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})
    with client.session_transaction() as sess:
        assert sess["customer_id"] == 42


def test_login_post_valid_sets_email_in_session(client, auth_service):
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})
    with client.session_transaction() as sess:
        assert sess["email"] == "a@b.co"


def test_login_post_invalid_rerenders_form(client, auth_service):
    auth_service.login.side_effect = ValueError("Invalid email or password.")
    with patch(_RENDER, return_value="form"):
        response = client.post("/login", data={"email": "a@b.co", "password": "wrong"})
    assert response.status_code == 200


def test_login_post_invalid_does_not_set_session(client, auth_service):
    auth_service.login.side_effect = ValueError("Invalid email or password.")
    with patch(_RENDER, return_value="form"):
        client.post("/login", data={"email": "a@b.co", "password": "wrong"})
    with client.session_transaction() as sess:
        assert "customer_id" not in sess


def test_login_post_missing_email_shows_error(client, auth_service):
    # The route validates presence of email before calling the service.
    with patch(_RENDER, return_value="form") as mock_render:
        client.post("/login", data={"email": "", "password": "Passw0rd"})
    _, kwargs = mock_render.call_args
    assert "email" in kwargs["errors"]
    auth_service.login.assert_not_called()


def test_login_post_missing_password_shows_error(client, auth_service):
    with patch(_RENDER, return_value="form") as mock_render:
        client.post("/login", data={"email": "a@b.co", "password": ""})
    _, kwargs = mock_render.call_args
    assert "password" in kwargs["errors"]
    auth_service.login.assert_not_called()


def test_login_post_missing_both_fields_shows_both_errors(client, auth_service):
    with patch(_RENDER, return_value="form") as mock_render:
        client.post("/login", data={"email": "", "password": ""})
    _, kwargs = mock_render.call_args
    assert "email" in kwargs["errors"]
    assert "password" in kwargs["errors"]
    auth_service.login.assert_not_called()


# ============================================================================
# GET /logout


def test_logout_redirects(client):
    response = client.get("/logout")
    assert response.status_code == 302


def test_logout_clears_session(client, auth_service):
    # Log in first so there is something to clear.
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})
    with client.session_transaction() as sess:
        assert "customer_id" in sess

    client.get("/logout")

    with client.session_transaction() as sess:
        assert "customer_id" not in sess
        assert "email" not in sess


def test_logout_preserves_cart(client, auth_service):
    # When logging out, the cart should be preserved so the user can continue
    # shopping without re-adding items to their cart.
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    with client.session_transaction() as sess:
        sess["cart"] = {"1": 2, "2": 1}

    client.get("/logout")

    with client.session_transaction() as sess:
        assert sess["cart"] == {"1": 2, "2": 1}


def test_logout_clears_login_but_preserves_empty_cart(client, auth_service):
    # Even if the cart is empty, the logout should still clear login info.
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})
    with client.session_transaction() as sess:
        sess["cart"] = {}

    client.get("/logout")

    with client.session_transaction() as sess:
        assert "customer_id" not in sess
        assert "email" not in sess
        assert sess.get("cart") == {} or "cart" not in sess


# ============================================================================
# Checkout login flow


def test_login_get_with_checkout_flag_renders_checkout_message(client):
    # When checkout_login_message is set in the session, the login page
    # should display the checkout message.
    with client.session_transaction() as sess:
        sess["checkout_login_message"] = True

    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/login")

    _, kwargs = mock_render.call_args
    assert kwargs["checkout_login"] is True


def test_login_get_without_checkout_flag_does_not_show_message(client):
    # When checkout_login_message is not set, the checkout message should
    # not be shown.
    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/login")

    _, kwargs = mock_render.call_args
    assert kwargs["checkout_login"] is False


def test_login_post_with_checkout_flag_redirects_to_checkout(client, auth_service):
    # When the user logs in with the checkout_login_message flag set,
    # they should be redirected to /checkout instead of home.
    with client.session_transaction() as sess:
        sess["checkout_login_message"] = True

    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    response = client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})

    assert response.status_code == 302
    assert "/checkout" in response.headers["Location"]


def test_login_post_with_checkout_flag_clears_flag_after_use(client, auth_service):
    # The checkout_login_message flag should be cleared after being used
    # so it doesn't persist to subsequent logins.
    with client.session_transaction() as sess:
        sess["checkout_login_message"] = True

    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})

    with client.session_transaction() as sess:
        assert "checkout_login_message" not in sess


def test_login_post_without_checkout_flag_redirects_to_homepage(client, auth_service):
    # Normal login (without the checkout flag) should redirect to home.
    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    response = client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


# ============================================================================
# Registration success flow


def test_login_get_with_registration_success_renders_message(client):
    # When registration_success flag is set in the session, the login page
    # should display the registration success message.
    with client.session_transaction() as sess:
        sess["registration_success"] = True

    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/login")

    _, kwargs = mock_render.call_args
    assert kwargs["registration_success"] is True


def test_login_post_with_registration_success_clears_flag(client, auth_service):
    # The registration_success flag should be cleared after login
    # so it doesn't persist to subsequent logins.
    with client.session_transaction() as sess:
        sess["registration_success"] = True

    auth_service.login.return_value = {"customer_id": 1, "email": "a@b.co"}
    client.post("/login", data={"email": "a@b.co", "password": "Passw0rd"})

    with client.session_transaction() as sess:
        assert "registration_success" not in sess
