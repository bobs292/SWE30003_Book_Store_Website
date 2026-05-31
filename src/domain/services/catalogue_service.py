class CatalogueService:
    def __init__(self, book_repository):
        self._book_repository = book_repository

    def list_books(self):
        return self._book_repository.list_books()

    def get_book(self, book_id):
        return self._book_repository.get_by_id(book_id)
