# ABC (Abstract Base Class) is a Python built-in that prevents a class from being
# instantiated directly. abstractmethod marks methods that subclasses must implement.
from abc import ABC, abstractmethod

# Abstract contract for customer data operations. The domain layer imports this class
# and never the concrete implementation. This means the business logic in the services
# has no knowledge of how or where customer data is stored. The concrete implementation
# is created in app.py and injected into the service, meaning the database can be
# swapped without changing any business logic.
class CustomerRepository(ABC):

    @abstractmethod
    def save(self, customer):
        # Persists a new customer to the data store.
        pass

    @abstractmethod
    def find_by_email(self, email):
        # Returns a Customer object matching the given email, or None if not found.
        pass

    @abstractmethod
    def find_by_id(self, customer_id):
        # Returns a Customer object matching the given id, or None if not found.
        pass