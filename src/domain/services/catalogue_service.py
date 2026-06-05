from src.domain.services.search_service import SearchService


class CatalogueService:
    VALID_SORT_OPTIONS = ["title", "author", "price-low", "price-high"]

    def __init__(self, book_repository):
        self._book_repository = book_repository

    def list_books(self):
        return self._book_repository.list_books()

    def get_book(self, book_id):
        return self._book_repository.get_by_id(book_id)

    def get_all_genres(self):
        """Returns sorted list of unique genres from all books."""
        books = self.list_books()
        genres = set(book.genre for book in books)
        return sorted(genres)

    def filter_by_genre(self, books, genre):
        """Filters books by genre. Returns all books if genre is empty."""
        if not genre or not genre.strip():
            return books
        genre = genre.strip()
        return [b for b in books if b.genre == genre]

    def sort_books(self, books, sort_by="title"):
        """
        Sorts books by specified criteria.

        Valid sort_by values: title, author, price-low, price-high
        Returns original list if sort_by is invalid.
        """
        sort_by = (sort_by or "title").strip()

        if sort_by == "price-low":
            return sorted(books, key=lambda b: float(b.price))
        elif sort_by == "price-high":
            return sorted(books, key=lambda b: float(b.price), reverse=True)
        elif sort_by == "author":
            return sorted(books, key=lambda b: b.author.lower())
        elif sort_by == "title":
            return sorted(books, key=lambda b: b.title.lower())
        else:
            return books

    def get_valid_sort_options(self):
        """Returns list of valid sort option values."""
        return self.VALID_SORT_OPTIONS.copy()

    def browse(self, search_query="", genre="", sort_by="title"):
        """Fetches, searches, filters, and sorts the catalogue in one call."""
        books = self.list_books()
        books = SearchService.search_books(books, search_query)
        books = self.filter_by_genre(books, genre)
        books = self.sort_books(books, sort_by)
        return books
