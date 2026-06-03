from abc import ABC, abstractmethod


class AddressGateway(ABC):
    @abstractmethod
    def validate(self, street, suburb, state, postcode) -> str | None:
        # Returns None if the address is valid, or an error message string.
        pass
