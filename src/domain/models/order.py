from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class OrderItem:
    book_id: int
    quantity: int
    unit_price: float

@dataclass
class Order:
    order_id: Optional[int] = None
    customer_id: int = None
    order_date: datetime = None
    total_amount: float = None
    shipping_address: str = None
    shipping_phone: str = None
    items: List[OrderItem] = field(default_factory=list)