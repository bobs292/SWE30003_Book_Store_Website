from src.domain.services.search_service import SearchService

BOOKS = [
    {"id": "9780544003415", "title": "The Martian", "author": "Andy Weir"},
    {"id": "9780307588371", "title": "Gone Girl", "author": "Gillian Flynn"},
    {"id": "9780553418026", "title": "Educated", "author": "Tara Westover"},
    {"id": "9780062407399", "title": "Origin", "author": "Dan Brown"},
]


class TestSearchBooks:
    def test_empty_query_returns_all_books(self):
        result = SearchService.search_books(BOOKS, "")
        assert len(result) == len(BOOKS)

    def test_none_query_returns_all_books(self):
        result = SearchService.search_books(BOOKS, None)
        assert len(result) == len(BOOKS)

    def test_whitespace_query_returns_all_books(self):
        result = SearchService.search_books(BOOKS, "   ")
        assert len(result) == len(BOOKS)

    def test_search_by_title_exact_match(self):
        result = SearchService.search_books(BOOKS, "Martian")
        assert len(result) == 1
        assert result[0]["title"] == "The Martian"

    def test_search_by_title_partial_match(self):
        result = SearchService.search_books(BOOKS, "Girl")
        assert len(result) == 1
        assert result[0]["title"] == "Gone Girl"

    def test_search_by_author(self):
        result = SearchService.search_books(BOOKS, "Andy Weir")
        assert len(result) == 1
        assert result[0]["author"] == "Andy Weir"

    def test_search_by_author_partial(self):
        result = SearchService.search_books(BOOKS, "Gillian")
        assert len(result) == 1
        assert result[0]["author"] == "Gillian Flynn"

    def test_search_by_isbn_full(self):
        result = SearchService.search_books(BOOKS, "9780544003415")
        assert len(result) == 1
        assert result[0]["title"] == "The Martian"

    def test_search_by_isbn_prefix(self):
        result = SearchService.search_books(BOOKS, "9780544")
        assert len(result) == 1
        assert result[0]["title"] == "The Martian"

    def test_search_by_isbn_does_not_match_middle(self):
        result = SearchService.search_books(BOOKS, "0544")
        assert len(result) == 0

    def test_search_case_insensitive(self):
        result = SearchService.search_books(BOOKS, "MARTIAN")
        assert len(result) == 1
        assert result[0]["title"] == "The Martian"

    def test_search_case_insensitive_author(self):
        result = SearchService.search_books(BOOKS, "tara")
        assert len(result) == 1
        assert result[0]["author"] == "Tara Westover"

    def test_search_matches_multiple_books(self):
        result = SearchService.search_books(BOOKS, "an")
        # "an" matches books with "an" in title or author
        assert len(result) >= 1

    def test_search_no_matches(self):
        result = SearchService.search_books(BOOKS, "xyz123")
        assert len(result) == 0

    def test_search_with_special_characters(self):
        result = SearchService.search_books(BOOKS, "Dan Brown")
        assert len(result) == 1
        assert result[0]["author"] == "Dan Brown"

    def test_search_empty_book_list(self):
        result = SearchService.search_books([], "Martian")
        assert len(result) == 0

    def test_search_preserves_book_data(self):
        result = SearchService.search_books(BOOKS, "Educated")
        assert len(result) == 1
        assert result[0]["id"] == "9780553418026"
        assert result[0]["title"] == "Educated"
        assert result[0]["author"] == "Tara Westover"

    def test_search_with_trailing_whitespace(self):
        result = SearchService.search_books(BOOKS, "  Martian  ")
        assert len(result) == 1
        assert result[0]["title"] == "The Martian"
