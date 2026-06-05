class SearchService:
    """Searches books by keyword, title, author, or ISBN."""

    @staticmethod
    def search_books(books, query):
        """
        Searches books by keyword matching in title, author, or ISBN.

        Performs case-insensitive partial matching.
        Returns all books if query is empty.
        """
        if not query or not query.strip():
            return books

        query = query.strip().lower()
        return [b for b in books if SearchService._matches_query(b, query)]

    @staticmethod
    def _matches_query(book, query):
        """Checks if a book matches the search query."""
        isbn = str(book.id).lower()
        title = book.title.lower()
        author = book.author.lower()

        isbn_match = isbn.startswith(query)
        title_match = query in title
        author_match = query in author

        return isbn_match or title_match or author_match
