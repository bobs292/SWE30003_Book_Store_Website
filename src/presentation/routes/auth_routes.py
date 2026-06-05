from flask import Blueprint, flash, redirect, render_template, request, session, url_for


def create_auth_routes(auth_service):
    auth = Blueprint("auth", __name__)

    @auth.route("/register", methods=["GET", "POST"])
    def register():
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
                    flash("Registration successful. Please log in.", "success")
                    return redirect(url_for("auth.login"))
                except ValueError as e:
                    flash(str(e), "error")

        return render_template("register.html", errors=errors, form=form)

    @auth.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            try:
                user = auth_service.login(
                    email=request.form.get("email"),
                    password=request.form.get("password"),
                )
                session["customer_id"] = user["customer_id"]
                session["email"] = user["email"]
                flash("Login successful.", "success")
                return redirect(url_for("homepage"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("login.html")

    @auth.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("homepage"))

    return auth
