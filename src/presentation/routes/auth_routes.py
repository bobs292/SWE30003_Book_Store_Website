"""Authentication routes for user registration, login, and logout.

Handles user account creation, credential validation, session management, and
cart persistence across authentication state changes.
"""

from flask import Blueprint, flash, redirect, render_template, request, session, url_for


def create_auth_routes(auth_service):
    """Create auth blueprint with registration, login, and logout routes.

    Args:
        auth_service: Service for user authentication and registration

    Returns:
        Flask Blueprint with authentication-related routes
    """
    auth = Blueprint("auth", __name__)

    @auth.route("/register", methods=["GET", "POST"])
    def register():
        """Handles user registration with email, password, and address validation.

        GET: Displays the registration form.
        POST: Validates input and creates a new user account.
        """
        errors = {}
        form = {}
        if request.method == "POST":
            form = request.form.to_dict()
            errors = auth_service.validate(
                email=form.get("email") or None,
                phone_number=form.get("phone_number") or None,
                password=form.get("password"),
                street=form.get("street") or None,
                suburb=form.get("suburb") or None,
                state=form.get("state") or None,
                postcode=form.get("postcode") or None,
            )
            if not (form.get("first_name") or "").strip():
                errors["first_name"] = "First name is required."
            if not (form.get("last_name") or "").strip():
                errors["last_name"] = "Last name is required."

            if not errors:
                try:
                    auth_service.register(
                        first_name=form.get("first_name"),
                        last_name=form.get("last_name"),
                        email=form.get("email"),
                        password=form.get("password"),
                        phone_number=form.get("phone_number") or None,
                        street=form.get("street") or None,
                        suburb=form.get("suburb") or None,
                        state=form.get("state") or None,
                        postcode=form.get("postcode") or None,
                    )
                    session["registration_success"] = True
                    return redirect(url_for("auth.login"))
                except ValueError as e:
                    flash(str(e), "error")

        return render_template("register.html", errors=errors, form=form)

    @auth.route("/login", methods=["GET", "POST"])
    def login():
        """Handles user login with email and password authentication.

        GET: Displays the login form.
        POST: Authenticates credentials and creates user session.
        """
        errors = {}
        form = {}
        checkout_login = session.get("checkout_login_message", False)
        registration_success = session.get("registration_success", False)

        if request.method == "POST":
            form = request.form.to_dict()
            email = form.get("email") or ""
            password = form.get("password") or ""

            if not email.strip():
                errors["email"] = "Email is required."
            if not password.strip():
                errors["password"] = "Password is required."

            if not errors:
                try:
                    user = auth_service.login(
                        email=email,
                        password=password,
                    )
                    session["customer_id"] = user["customer_id"]
                    session["email"] = user["email"]
                    flash("Login successful.", "success")
                    if checkout_login:
                        session.pop("checkout_login_message", None)
                    session.pop("registration_success", None)
                    redirect_url = (
                        url_for("order.checkout")
                        if checkout_login
                        else url_for("homepage")
                    )
                    return redirect(redirect_url)
                except ValueError as e:
                    errors["login"] = str(e)

        return render_template(
            "login.html",
            errors=errors,
            form=form,
            checkout_login=checkout_login,
            registration_success=registration_success,
        )

    @auth.route("/logout")
    def logout():
        """Clears user session while preserving the shopping cart state."""
        cart = session.get("cart")
        session.clear()
        if cart:
            session["cart"] = cart
        return redirect(url_for("homepage"))

    return auth
