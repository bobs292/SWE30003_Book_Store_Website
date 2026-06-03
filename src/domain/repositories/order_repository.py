from abc import ABC, abstractmethod
from src.domain.models.order import Order

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order: Order) -> Order:
        """Persist order and return with generated order_id"""
        pass

    @abstractmethod
    def find_by_id(self, order_id: int) -> Order | None:
        pass