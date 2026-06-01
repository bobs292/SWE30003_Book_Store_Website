# ABC (Abstract Base Class) is a Python built-in that prevents a class from being
# instantiated directly. abstractmethod marks methods that subclasses must implement.
from abc import ABC, abstractmethod


# Abstract contract for book data operations. The domain layer imports this class
# and never the concrete implementation. This means the business logic in the services
# has no knowledge of how or where book data is stored. The concrete implementation
# is created in app.py and injected into the service, meaning the database can be
# swapped without changing any business logic.
class BookRepository(ABC):

    @abstractmethod
    def list_books(self):
        # Returns all books from the data store as a list.
        pass

    @abstractmethod
    def get_by_id(self, book_id):
        # Returns a single book matching the given id, or None if not found.
        pass
