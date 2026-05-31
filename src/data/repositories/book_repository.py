import os
from src.domain.repositories.book_repository import BookRepository
from src.data.database import get_connection


class SqliteBookRepository(BookRepository):

    def list_books(self):
        # Returns all books from the database as a list of dictionaries.
        # Each dictionary matches the shape the catalogue service and cart
        # routes expect.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books')
        rows = cursor.fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def get_by_id(self, book_id):
        # Returns a single book by its id, or None if it does not exist.
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM books WHERE book_id = ?', (book_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_dict(row)

    def _row_to_dict(self, row):
        # Converts a database row into a plain dictionary.
        # The id key maps to book_id so the rest of the application does not
        # need to know the internal column name.
        # cover_url is derived from the isbn at query time using the Open Library
        # Covers API. isbn remains in the database as a business attribute
        # identifying the specific edition. If isbn is null, cover_url is None
        # and the template falls back to a placeholder.
        isbn = row['isbn']
        # Use the locally cached cover if it exists.
        # The cache is populated at seed time by cover_cache.py.
        # If the file does not exist the template falls back to a placeholder.
        if isbn:
            cache_path = os.path.join(
                os.path.dirname(__file__), '..', '..',
                'presentation', 'static', 'images', 'covers', f'{isbn}.jpg'
            )
            cover_url = f'/static/images/covers/{isbn}.jpg' if os.path.exists(cache_path) else None
        else:
            cover_url = None
        return {
            'id': row['book_id'],
            'title': row['title'],
            'author': row['author'],
            'isbn': isbn,
            'genre': row['genre'],
            'description': row['description'],
            'cover_url': cover_url,
            'price': row['price'],
            'stock': row['stock'],
        }
