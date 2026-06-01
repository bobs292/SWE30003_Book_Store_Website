# Flask is the web framework. render_template renders HTML templates
# from the templates folder.
import os

from flask import Flask, render_template, session

# init_db creates the database tables on startup.
from src.data.database import init_db

# Concrete repository for loading books from JSON.
from src.data.repositories.book_repository import SqliteBookRepository

# The only concrete repository imported in this file. All other layers
# reference the abstract contract.
from src.data.repositories.customer_repository import SqliteCustomerRepository

# The auth service contains the business logic for login and registration.
from src.domain.services.auth_service import AuthService

# Catalogue service provides book data for browsing and cart operations.
from src.domain.services.catalogue_service import CatalogueService

# Factory functions that create blueprints with services injected.
from src.presentation.routes.auth_routes import create_auth_routes
from src.presentation.routes.catalogue_routes import create_catalogue_routes
from src.presentation.routes.order_routes import create_order_routes


def create_app():
    # Initialises the Flask app, telling it where to find the HTML templates
    # and static files relative to the src/ directory.
    app = Flask(
        __name__,
        template_folder="presentation/templates",
        static_folder="presentation/static",
    )

    # Required by Flask to cryptographically sign session cookies so that
    # session data cannot be tampered with by the client. Hardcoded for development.
    app.secret_key = "your-secret-key-here"

    # Runs once on startup. Creates the database file and all tables if they
    # do not already exist. Does nothing if they are already there.
    # The cover cache directory is passed in so the data layer can save images
    # without knowing anything about Flask's static folder structure.
    cover_cache_dir = os.path.join(
        os.path.dirname(__file__), "presentation", "static", "images", "covers"
    )
    init_db(cover_cache_dir)

    # Instantiates the SQLite customer repository, creating a live object
    # from the class blueprint that can run queries against the database.
    # This is the only place in the project where this class is named directly.
    customer_repo = SqliteCustomerRepository()

    # Instantiates the auth service, injecting the customer repository so
    # the service can access customer data without knowing it is backed by SQLite.
    auth_service = AuthService(customer_repo)

    # Creates the catalogue service by injecting the JSON book repository.
    book_repo = SqliteBookRepository()
    catalogue_service = CatalogueService(book_repo)

    # Creates the auth routes with the auth service injected, then registers
    # them with Flask so the app knows to handle incoming requests to
    # /login, /register and /logout.
    app.register_blueprint(create_auth_routes(auth_service))

    # Registers the catalogue routes with the catalogue service injected.
    app.register_blueprint(create_catalogue_routes(catalogue_service))

    # Registers the order routes with the catalogue service injected.
    app.register_blueprint(create_order_routes(catalogue_service))

    # Registers the homepage route directly on the app rather than a blueprint
    # as it does not belong to any specific area of the application.
    @app.route("/")
    def homepage():
        return render_template("home.html")

    @app.context_processor
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

    return app


# Calls create_app() to produce the Flask application instance that the
# Flask dev server looks for when running flask run.
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
