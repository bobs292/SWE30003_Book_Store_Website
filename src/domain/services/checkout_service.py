"""Order processing and checkout management.

Handles the complete checkout workflow: stock validation, payment processing,
order and invoice creation, and inventory updates.
"""

from datetime import datetime

from src.domain.models.invoice import Invoice
from src.domain.models.order import Order, OrderItem
from src.domain.repositories.book_repository import BookRepository
from src.domain.repositories.invoice_repository import InvoiceRepository
from src.domain.repositories.order_repository import OrderRepository
from src.domain.repositories.payment_gateway import PaymentGateway


class CheckoutService:
    """Manages the order checkout process and invoice generation."""

    def __init__(
        self,
        order_repo: OrderRepository,
        invoice_repo: InvoiceRepository,
        book_repo: BookRepository,
        payment_gateway: PaymentGateway,
    ):
        """Initializes checkout service with required repositories and payment gateway.

        Args:
            order_repo: Repository for saving orders
            invoice_repo: Repository for saving invoices
            book_repo: Repository for book stock management
            payment_gateway: Payment processor for charging customers
        """
        self.order_repo = order_repo
        self.invoice_repo = invoice_repo
        self.book_repo = book_repo
        self.payment_gateway = payment_gateway

    STANDARD_SHIPPING_FEE = 9.99

    def process_checkout(
        self,
        customer_id: int,
        cart_items: list,
        shipping_address: str,
        shipping_phone: str,
        payment_details: dict,
        shipping_fee: float = 9.99,
    ):
        """Process checkout: validate stock, charge payment, create order.

        Validates book availability, charges the customer, creates an order and
        invoice, and updates inventory. Raises ValueError if books are unavailable
        or payment fails.

        Args:
            customer_id: ID of the customer making the purchase
            cart_items: List of dicts with book_id, quantity, unit_price
            shipping_address: Full shipping address or "Store Pickup"
            shipping_phone: Customer phone number for delivery (nullable)
            payment_details: Payment info (unused in current implementation)
            shipping_fee: Shipping cost (0.0 for store pickup)

        Returns:
            Tuple of (Order, Invoice) for the successful transaction

        Raises:
            ValueError: If book not found or stock is insufficient
            Exception: If payment processing fails
        """
        # ensure stock is available and fetch book objects
        books = {}
        for item in cart_items:
            book = self.book_repo.get_by_id(item["book_id"])
            if not book:
                raise ValueError(f"Book {item['book_id']} not found")
            if book["stock"] < item["quantity"]:
                raise ValueError(f"Insufficient stock for '{book['title']}'")
            books[item["book_id"]] = book

        subtotal = sum(item["quantity"] * item["unit_price"] for item in cart_items)
        total = subtotal + shipping_fee

        # process payment
        if not self.payment_gateway.charge(total, payment_details):
            raise Exception("Payment failed")

        # create the order items
        order_items = [
            OrderItem(
                book_id=item["book_id"],
                quantity=item["quantity"],
                unit_price=item["unit_price"],
            )
            for item in cart_items
        ]

        # create the order with order items
        order = Order(
            customer_id=customer_id,
            order_date=datetime.now(),
            total_amount=total,
            shipping_address=shipping_address,
            shipping_phone=shipping_phone,
            items=order_items,
        )
        saved_order = self.order_repo.save(order)

        # create Invoice
        invoice = Invoice(
            order_id=saved_order.order_id,
            invoice_date=datetime.now(),
            amount_due=total,
        )
        saved_invoice = self.invoice_repo.save(invoice)

        # update stock, reduce by quantitiy
        for item in cart_items:
            book = books[item["book_id"]]
            book["stock"] -= item["quantity"]
            self.book_repo.update(book)

        return saved_order, saved_invoice
