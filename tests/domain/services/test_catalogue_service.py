from unittest.mock import MagicMock

from src.domain.services.catalogue_service import CatalogueService

BOOKS = [
    {"id": "9780553418026", "title": "The Martian", "price": 18.99, "stock": 5},
    {"id": "9780307588371", "title": "Gone Girl", "price": 19.99, "stock": 0},
]


def _make_repo(books=None):
    _books = BOOKS if books is None else books
    repo = MagicMock()
    repo.list_books.return_value = _books
    repo.get_by_id.side_effect = lambda book_id: next(
        (b for b in _books if b["id"] == book_id), None
    )
    return repo


# ============================================================================
# list_books


def test_list_books_delegates_to_repository():
    repo = _make_repo()
    CatalogueService(repo).list_books()
    repo.list_books.assert_called_once()


def test_list_books_returns_all_books():
    assert len(CatalogueService(_make_repo()).list_books()) == 2


def test_list_books_returns_empty_list_when_catalogue_empty():
    assert CatalogueService(_make_repo(books=[])).list_books() == []


def test_list_books_returns_repository_result_unchanged():
    repo = _make_repo()
    result = CatalogueService(repo).list_books()
    assert result is repo.list_books.return_value


# ============================================================================
# get_book


def test_get_book_delegates_to_repository():
    repo = _make_repo()
    CatalogueService(repo).get_book("9780553418026")
    repo.get_by_id.assert_called_once_with("9780553418026")


def test_get_book_returns_matching_book():
    result = CatalogueService(_make_repo()).get_book("9780553418026")
    assert result["title"] == "The Martian"


def test_get_book_returns_none_for_missing_id():
    assert CatalogueService(_make_repo()).get_book("0000000000000") is None
