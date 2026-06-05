"""Invoice domain model for order billing."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Invoice:
    """Represents a billing invoice for an order.

    Attributes:
        invoice_id: Unique invoice identifier (None until saved)
        order_id: ID of the associated order
        invoice_date: Timestamp when invoice was generated
        amount_due: Total amount charged for the order
    """

    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    invoice_date: Optional[datetime] = None
    amount_due: Optional[float] = None
