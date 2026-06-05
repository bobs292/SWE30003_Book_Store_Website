"""Catalogue routes for browsing and searching books.

Supports browsing all books, filtering by genre, sorting by various criteria,
and searching by title, author, or ISBN.
"""

from flask import Blueprint, abort, render_template, request, session

from src.domain.services.cart_service import CartService


def create_catalogue_routes(catalogue_service):
    """Creates and returns the catalogue blueprint with browsing and search routes.

    Args:
        catalogue_service: Service for accessing book data and metadata

    Returns:
        Flask Blueprint with catalogue-related routes
    """
    catalogue = Blueprint("catalogue", __name__)

    @catalogue.route("/catalogue")
    def catalogue_page():
        """Displays the book catalogue with search, genre filtering, and sorting."""
        genres = catalogue_service.get_all_genres()

        search_query = request.args.get("search", "").strip()
        selected_genre = request.args.get("genre", "").strip()
        sort_by = request.args.get("sort", "title").strip()

        books = catalogue_service.browse(search_query, selected_genre, sort_by)
        cart_data = CartService.normalize_cart(session.get("cart"))

        return render_template(
            "catalogue.html",
            books=books,
            genres=genres,
            selected_genre=selected_genre,
            sort_by=sort_by,
            search_query=search_query,
            cart=cart_data,
        )

    @catalogue.route("/book/<isbn>")
    def book_detail(isbn):
        """Displays detailed information for a single book by ISBN."""
        book = catalogue_service.get_book(isbn)
        if book is None:
            abort(404)
        cart_data = CartService.normalize_cart(session.get("cart"))
        return render_template("book_detail.html", book=book, cart=cart_data)

    return catalogue
