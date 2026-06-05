"""Order and order item domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class OrderItem:
    """Represents a single book in an order.

    Attributes:
        book_id: ID of the book in the order
        quantity: Number of copies ordered
        unit_price: Price per copy at time of order
    """

    book_id: int
    quantity: int
    unit_price: float


@dataclass
class Order:
    """Represents a complete customer order.

    Attributes:
        order_id: Unique order identifier (None until saved)
        customer_id: ID of the customer who placed the order
        order_date: Timestamp when order was created
        total_amount: Total price including shipping
        shipping_address: Delivery address or "Store Pickup"
        shipping_phone: Customer phone number for delivery (nullable)
        items: List of OrderItem objects in the order
    """

    order_id: Optional[int] = None
    customer_id: Optional[int] = None
    order_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    shipping_address: Optional[str] = None
    shipping_phone: Optional[str] = None
    items: List[OrderItem] = field(default_factory=list)
