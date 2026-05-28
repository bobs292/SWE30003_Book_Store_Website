from abc import ABC, abstractmethod

class User(ABC):
    def __init__(self, name, address, phone_number, password):
        self.name = name
        self.address = address
        self.phone_number = phone_number
        self.password = password
