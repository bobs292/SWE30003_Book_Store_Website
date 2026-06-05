import os

from src.data.database import get_connection
from src.domain.repositories.book_repository import BookRepository


class SqliteBookRepository(BookRepository):

    def list_books(self):
        # Returns all books from the database as a list of dictionaries.
        # Each dictionary matches the shape the catalogue service and cart
        # routes expect.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def get_by_id(self, book_id):
        # Returns a single book by its isbn, or None if it does not exist.
        # The parameter is named book_id for continuity with the domain
        # contract, but since isbn is now the primary key the value passed
        # in is the book's isbn.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE isbn = ?", (book_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_dict(row)

    # updates changes to the book recorod
    def update(self, book):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET stock = ? WHERE isbn = ?", (book["stock"], book["id"])
        )
        conn.commit()
        conn.close()

    def _row_to_dict(self, row):
        # Converts a database row into a plain dictionary.
        # isbn is the primary key, so the id key the rest of the application
        # uses maps to isbn. The rest of the app treats id as an opaque
        # string (it is only ever passed through cart forms and compared as
        # a string), so it does not need to know the key is an isbn.
        # cover_url is derived from the isbn at query time using the Open
        # Library Covers API.
        isbn = row["isbn"]
        # Use the locally cached cover if it exists.
        # The cache is populated at seed time by cover_cache.py.
        # If the file does not exist the template falls back to a placeholder.
        # Build the filesystem path to the locally cached cover image.
        # __file__ resolves to src/data/repositories/book_repository.py.
        # Each '..' moves up one directory level: first to src/data,
        # then to src/. From there we navigate into
        # presentation/static/images/covers/{isbn}.jpg.
        # This relative construction keeps the path correct regardless
        # of where the project is cloned on disk.
        cache_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "presentation",
            "static",
            "images",
            "covers",
            f"{isbn}.jpg",
        )
        cover_url = (
            f"/static/images/covers/{isbn}.jpg" if os.path.exists(cache_path) else None
        )
        return {
            "id": isbn,
            "title": row["title"],
            "author": row["author"],
            "isbn": isbn,
            "genre": row["genre"],
            "description": row["description"],
            "cover_url": cover_url,
            "price": row["price"],
            "stock": row["stock"],
        }
