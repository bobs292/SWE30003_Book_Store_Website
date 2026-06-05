from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Invoice:
    invoice_id: Optional[int] = None
    order_id: int = None
    invoice_date: datetime = None
    amount_due: float = None