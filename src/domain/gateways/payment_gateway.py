from abc import ABC, abstractmethod


class PaymentGateway(ABC):
    @abstractmethod
    def charge(self, amount: float, payment_details: dict) -> bool:
        """Return True if payment succeeded, False otherwise."""
        pass
