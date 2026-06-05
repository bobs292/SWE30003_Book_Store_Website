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


# ============================================================================
# get_all_genres


def test_get_all_genres_returns_sorted_unique():
    books = [
        {"id": 1, "title": "Book 1", "genre": "Fantasy"},
        {"id": 2, "title": "Book 2", "genre": "Science Fiction"},
        {"id": 3, "title": "Book 3", "genre": "Fantasy"},
        {"id": 4, "title": "Book 4", "genre": "Dystopian"},
    ]
    repo = _make_repo(books)
    genres = CatalogueService(repo).get_all_genres()

    assert genres == ["Dystopian", "Fantasy", "Science Fiction"]


def test_get_all_genres_empty_catalogue():
    repo = _make_repo([])
    genres = CatalogueService(repo).get_all_genres()

    assert genres == []


# ============================================================================
# filter_by_genre


def test_filter_by_genre_filters_correctly():
    books = [
        {"id": 1, "title": "Book 1", "genre": "Fantasy"},
        {"id": 2, "title": "Book 2", "genre": "Science Fiction"},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.filter_by_genre(books, "Fantasy")

    assert len(result) == 1
    assert result[0]["title"] == "Book 1"


def test_filter_by_genre_empty_returns_all():
    books = [
        {"id": 1, "title": "Book 1", "genre": "Fantasy"},
        {"id": 2, "title": "Book 2", "genre": "Science Fiction"},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.filter_by_genre(books, "")

    assert len(result) == 2


# ============================================================================
# sort_books


def test_sort_books_by_title():
    books = [
        {"id": 2, "title": "Zebra", "author": "Author A", "price": 10},
        {"id": 1, "title": "Apple", "author": "Author B", "price": 20},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.sort_books(books, "title")

    assert result[0]["title"] == "Apple"
    assert result[1]["title"] == "Zebra"


def test_sort_books_by_author():
    books = [
        {"id": 1, "title": "Book 1", "author": "Zoe", "price": 10},
        {"id": 2, "title": "Book 2", "author": "Alice", "price": 20},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.sort_books(books, "author")

    assert result[0]["author"] == "Alice"
    assert result[1]["author"] == "Zoe"


def test_sort_books_by_price_low():
    books = [
        {"id": 1, "title": "Book 1", "author": "Author A", "price": 20},
        {"id": 2, "title": "Book 2", "author": "Author B", "price": 10},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.sort_books(books, "price-low")

    assert result[0]["price"] == 10
    assert result[1]["price"] == 20


def test_sort_books_by_price_high():
    books = [
        {"id": 1, "title": "Book 1", "author": "Author A", "price": 20},
        {"id": 2, "title": "Book 2", "author": "Author B", "price": 10},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.sort_books(books, "price-high")

    assert result[0]["price"] == 20
    assert result[1]["price"] == 10


def test_sort_books_invalid_returns_original():
    books = [
        {"id": 2, "title": "Zebra"},
        {"id": 1, "title": "Apple"},
    ]
    service = CatalogueService(_make_repo(books))
    result = service.sort_books(books, "invalid")

    assert result == books


def test_get_valid_sort_options():
    service = CatalogueService(_make_repo())
    options = service.get_valid_sort_options()

    assert options == ["title", "author", "price-low", "price-high"]
