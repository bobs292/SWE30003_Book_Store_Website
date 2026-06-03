from datetime import datetime
from src.domain.models.order import Order, OrderItem
from src.domain.models.invoice import Invoice
from src.domain.repositories.order_repository import OrderRepository
from src.domain.repositories.invoice_repository import InvoiceRepository
from src.domain.repositories.book_repository import BookRepository
from src.domain.repositories.payment_gateway import PaymentGateway

class CheckoutService:
    def __init__(
        self,
        order_repo: OrderRepository,
        invoice_repo: InvoiceRepository,
        book_repo: BookRepository,
        payment_gateway: PaymentGateway,
    ):
        self.order_repo = order_repo
        self.invoice_repo = invoice_repo
        self.book_repo = book_repo
        self.payment_gateway = payment_gateway

    def process_checkout(
        self,
        customer_id: int,
        cart_items: list,
        shipping_address: str,
        shipping_phone: str,
        payment_details: dict,
    ):
        # ensure stock is available and fetch book objects
        books = {}
        for item in cart_items:
            book = self.book_repo.get_by_id(item["book_id"])
            if not book:
                raise ValueError(f"Book {item['book_id']} not found")
            if book["stock"] < item["quantity"]:
                raise ValueError(f"Insufficient stock for '{book.title}'")
            books[item["book_id"]] = book

        # Calculate the total (add flat shipping fee $9.99)
        subtotal = sum(item["quantity"] * item["unit_price"] for item in cart_items)
        total = subtotal + 9.99

        # prrocess payment
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