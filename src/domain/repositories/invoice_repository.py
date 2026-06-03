from abc import ABC, abstractmethod
from src.domain.models.invoice import Invoice

class InvoiceRepository(ABC):
    @abstractmethod
    def save(self, invoice: Invoice) -> Invoice:
        pass