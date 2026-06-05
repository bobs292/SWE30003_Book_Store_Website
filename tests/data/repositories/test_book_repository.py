# tests/data/repositories/test_book_repository.py
from unittest.mock import MagicMock, patch

from src.data.repositories.book_repository import SqliteBookRepository


class TestSqliteBookRepository:
    """Tests for the SQLite-backed book repository."""

    def test_list_books_returns_all_books(self):
        # list_books should return every row in the books table as a dict.
        fake_rows = [
            {
                "title": "Book A",
                "author": "Author A",
                "isbn": "111",
                "genre": "Fiction",
                "description": "Desc A",
                "price": 9.99,
                "stock": 5,
            },
            {
                "title": "Book B",
                "author": "Author B",
                "isbn": "222",
                "genre": "Non-Fiction",
                "description": "Desc B",
                "price": 12.50,
                "stock": 3,
            },
        ]

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            repo = SqliteBookRepository()
            books = repo.list_books()

        assert len(books) == 2
        assert books[0].title == "Book A"
        assert books[1].title == "Book B"

    def test_get_by_id_returns_correct_book(self):
        # get_by_id should return the matching book with id and cover_url set.
        fake_row = {
            "title": "Book A",
            "author": "Author A",
            "isbn": "111",
            "genre": "Fiction",
            "description": "Desc A",
            "price": 9.99,
            "stock": 5,
        }

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch(
                "src.data.repositories.book_repository.os.path.exists",
                return_value=True,
            ):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)
        assert book is not None
        assert book.id == "111"
        assert book.title == "Book A"

    def test_get_by_id_returns_none_for_missing_id(self):
        # When no row matches the given id, get_by_id should return None.
        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = None
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            repo = SqliteBookRepository()
            book = repo.get_by_id(999)
        assert book is None

    def test_cover_url_set_when_cached_file_exists(self):
        # If the locally cached cover image exists on disk, cover_url should
        # point to the static image route so the template can render it.
        fake_row = {
            "title": "Book A",
            "author": "Author A",
            "isbn": "9780140449136",
            "genre": "Fiction",
            "description": "Desc A",
            "price": 9.99,
            "stock": 5,
        }

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch(
                "src.data.repositories.book_repository.os.path.exists",
                return_value=True,
            ):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)

        assert book.cover_url == "/static/images/covers/9780140449136.jpg"

    def test_update_uses_isbn_column(self):
        # update() must use the isbn column, not a non-existent book_id column.
        # This test would have caught the original bug where the query used
        # "WHERE book_id = ?" and raised "no such column: book_id" at runtime.
        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.cursor.return_value = mock_cursor

            repo = SqliteBookRepository()
            from src.domain.models.book_title import Book

            repo.update(Book(id="9780553418026", stock=3))

        sql = mock_cursor.execute.call_args[0][0]
        assert "isbn" in sql.lower()
        assert "book_id" not in sql.lower()

    def test_update_passes_stock_and_isbn(self):
        # The correct stock value and isbn must be bound to the query parameters.
        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_conn.return_value.cursor.return_value = mock_cursor

            repo = SqliteBookRepository()
            from src.domain.models.book_title import Book

            repo.update(Book(id="9780553418026", stock=7))

        params = mock_cursor.execute.call_args[0][1]
        assert params[0] == 7  # new stock
        assert params[1] == "9780553418026"  # isbn used as key

    def test_cover_url_none_when_cached_file_does_not_exist(self):
        # If the cover has not been cached locally, cover_url should be None
        # so the template falls back to a placeholder image.
        fake_row = {
            "title": "Book A",
            "author": "Author A",
            "isbn": "9780140449136",
            "genre": "Fiction",
            "description": "Desc A",
            "price": 9.99,
            "stock": 5,
        }

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch(
                "src.data.repositories.book_repository.os.path.exists",
                return_value=False,
            ):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)

        assert book.cover_url is None
