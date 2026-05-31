# tests/data/repositories/test_book_repository.py
import os
from unittest.mock import patch, MagicMock

import pytest

from src.data.repositories.book_repository import SqliteBookRepository


class TestSqliteBookRepository:
    """Tests for the SQLite-backed book repository."""

    def test_list_books_returns_all_books(self):
        # list_books should return every row in the books table as a dict.
        fake_rows = [
            {"book_id": 1, "title": "Book A", "author": "Author A",
             "isbn": "111", "genre": "Fiction", "description": "Desc A",
             "price": 9.99, "stock": 5},
            {"book_id": 2, "title": "Book B", "author": "Author B",
             "isbn": "222", "genre": "Non-Fiction", "description": "Desc B",
             "price": 12.50, "stock": 3},
        ]

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = fake_rows
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            repo = SqliteBookRepository()
            books = repo.list_books()

        assert len(books) == 2
        assert books[0]["title"] == "Book A"
        assert books[1]["title"] == "Book B"

    def test_get_by_id_returns_correct_book(self):
        # get_by_id should return the matching book with id and cover_url set.
        fake_row = {"book_id": 1, "title": "Book A", "author": "Author A",
                    "isbn": "111", "genre": "Fiction", "description": "Desc A",
                    "price": 9.99, "stock": 5}

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch("src.data.repositories.book_repository.os.path.exists", return_value=True):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)

        assert book is not None
        assert book["id"] == 1
        assert book["title"] == "Book A"

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
        fake_row = {"book_id": 1, "title": "Book A", "author": "Author A",
                    "isbn": "9780140449136", "genre": "Fiction",
                    "description": "Desc A", "price": 9.99, "stock": 5}

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch("src.data.repositories.book_repository.os.path.exists", return_value=True):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)

        assert book["cover_url"] == "/static/images/covers/9780140449136.jpg"

    def test_cover_url_none_when_cached_file_does_not_exist(self):
        # If the cover has not been cached locally, cover_url should be None
        # so the template falls back to a placeholder image.
        fake_row = {"book_id": 1, "title": "Book A", "author": "Author A",
                    "isbn": "9780140449136", "genre": "Fiction",
                    "description": "Desc A", "price": 9.99, "stock": 5}

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            with patch("src.data.repositories.book_repository.os.path.exists", return_value=False):
                repo = SqliteBookRepository()
                book = repo.get_by_id(1)

        assert book["cover_url"] is None

    def test_cover_url_none_when_isbn_is_null(self):
        # When the database row has no ISBN, no cover can be fetched.
        # cover_url should be None regardless of what exists on disk.
        fake_row = {"book_id": 1, "title": "Book A", "author": "Author A",
                    "isbn": None, "genre": "Fiction", "description": "Desc A",
                    "price": 9.99, "stock": 5}

        with patch("src.data.repositories.book_repository.get_connection") as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = fake_row
            mock_conn.return_value.cursor.return_value = mock_cursor
            mock_conn.return_value.close = MagicMock()

            repo = SqliteBookRepository()
            book = repo.get_by_id(1)

        assert book["cover_url"] is None
