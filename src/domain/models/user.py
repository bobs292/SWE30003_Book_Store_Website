# ABC (Abstract Base Class) is a Python built-in that prevents a class from being
# instantiated directly. abstractmethod marks methods that subclasses must implement.
from abc import ABC


# Defines the shared attributes that all users have regardless of their role.
# Never instantiated directly. Customer and Admin inherit from this class.
class User(ABC):
    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
