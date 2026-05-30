from flask import Blueprint, render_template


def create_catalogue_routes(catalogue_service):
    catalogue = Blueprint('catalogue', __name__)

    @catalogue.route('/catalogue')
    def catalogue_page():
        books = catalogue_service.list_books()
        return render_template('catalogue.html', books=books)

    return catalogue
