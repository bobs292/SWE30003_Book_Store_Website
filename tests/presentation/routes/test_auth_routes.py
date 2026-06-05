from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

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
    mock_render.assert_called_once_with("register.html")


# ============================================================================
# POST /register


def test_register_post_valid_redirects_to_login(client, auth_service):
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


def test_register_post_calls_service_with_form_fields(client, auth_service):
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
    # When the service raises ValueError the route must re-render the form
    # (200) rather than redirecting, so the user can correct their input.
    auth_service.register.side_effect = ValueError("Password must contain...")
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
    auth_service.register.side_effect = ValueError("error")
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
    mock_render.assert_called_once_with("register.html")


# ============================================================================
# GET /login


def test_login_get_returns_200(client):
    with patch(_RENDER, return_value="form"):
        response = client.get("/login")
    assert response.status_code == 200


def test_login_get_renders_login_template(client):
    with patch(_RENDER, return_value="form") as mock_render:
        client.get("/login")
    mock_render.assert_called_once_with("login.html")


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
