import os

from src.data.database import get_connection
from src.domain.models.book_title import Book
from src.domain.repositories.book_repository import BookRepository


class SqliteBookRepository(BookRepository):

    def list_books(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books")
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_book(row) for row in rows]

    def get_by_id(self, book_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM books WHERE isbn = ?", (book_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_book(row)

    def update(self, book: Book):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET stock = ? WHERE isbn = ?", (book.stock, book.id)
        )
        conn.commit()
        conn.close()

    def _row_to_book(self, row) -> Book:
        isbn = row["isbn"]
        # Build the filesystem path to the locally cached cover image.
        # __file__ resolves to src/data/repositories/book_repository.py.
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
        return Book(
            id=isbn,
            title=row["title"],
            author=row["author"],
            genre=row["genre"],
            description=row["description"],
            price=row["price"],
            stock=row["stock"],
            cover_url=cover_url,
        )
