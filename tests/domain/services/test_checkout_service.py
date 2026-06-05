from unittest.mock import MagicMock

import pytest

from src.domain.models.invoice import Invoice
from src.domain.models.order import Order
from src.domain.services.checkout_service import CheckoutService

# ============================================================================
# Stubs


def _make_book(book_id, title="Test Book", stock=10, price=19.99):
    return {"id": book_id, "title": title, "price": price, "stock": stock}


def _make_book_repo(*books):
    index = {b["id"]: dict(b) for b in books}  # copy so stock mutations are visible
    repo = MagicMock()
    repo.get_by_id.side_effect = lambda book_id: index.get(book_id)
    repo.update.side_effect = lambda book: index.update({book["id"]: book})
    return repo


def _make_order_repo(order_id=1):
    repo = MagicMock()

    def _save(order):
        order.order_id = order_id
        return order

    repo.save.side_effect = _save
    return repo


def _make_invoice_repo(invoice_id=1):
    repo = MagicMock()

    def _save(invoice):
        invoice.invoice_id = invoice_id
        return invoice

    repo.save.side_effect = _save
    return repo


def _make_payment_gateway(succeeds=True):
    gw = MagicMock()
    gw.charge.return_value = succeeds
    return gw


def _make_service(books=None, order_id=1, invoice_id=1, payment_succeeds=True):
    _books = books if books is not None else [_make_book(1)]
    return CheckoutService(
        order_repo=_make_order_repo(order_id),
        invoice_repo=_make_invoice_repo(invoice_id),
        book_repo=_make_book_repo(*_books),
        payment_gateway=_make_payment_gateway(payment_succeeds),
    )


CART = [{"book_id": 1, "quantity": 2, "unit_price": 19.99}]


# ============================================================================
# Stock and book validation


def test_raises_if_book_not_found():
    service = _make_service(books=[])
    with pytest.raises(ValueError, match="not found"):
        service.process_checkout(1, CART, "1 Main St", "0412345678", {})


def test_raises_if_insufficient_stock():
    service = _make_service(books=[_make_book(1, stock=1)])
    cart = [{"book_id": 1, "quantity": 2, "unit_price": 19.99}]
    with pytest.raises(ValueError, match="Insufficient stock"):
        service.process_checkout(1, cart, "1 Main St", "0412345678", {})


def test_insufficient_stock_error_contains_book_title():
    service = _make_service(books=[_make_book(1, title="Gone Girl", stock=0)])
    with pytest.raises(ValueError, match="Gone Girl"):
        service.process_checkout(1, CART, "1 Main St", "0412345678", {})


def test_exact_stock_available_does_not_raise():
    # Quantity exactly equal to stock must be accepted.
    service = _make_service(books=[_make_book(1, stock=2)])
    cart = [{"book_id": 1, "quantity": 2, "unit_price": 19.99}]
    service.process_checkout(1, cart, "1 Main St", "0412345678", {})


# ============================================================================
# Payment


def test_raises_if_payment_fails():
    service = _make_service(payment_succeeds=False)
    with pytest.raises(Exception, match="Payment failed"):
        service.process_checkout(1, CART, "1 Main St", "0412345678", {})


def test_payment_gateway_charged_with_correct_total():
    gw = _make_payment_gateway()
    service = CheckoutService(
        order_repo=_make_order_repo(),
        invoice_repo=_make_invoice_repo(),
        book_repo=_make_book_repo(_make_book(1)),
        payment_gateway=gw,
    )
    cart = [{"book_id": 1, "quantity": 2, "unit_price": 19.99}]
    service.process_checkout(1, cart, "1 Main St", "0412345678", {"card": "4111"})
    charged = gw.charge.call_args[0][0]
    assert abs(charged - (2 * 19.99 + 9.99)) < 0.001


def test_payment_gateway_receives_payment_details():
    gw = _make_payment_gateway()
    service = CheckoutService(
        order_repo=_make_order_repo(),
        invoice_repo=_make_invoice_repo(),
        book_repo=_make_book_repo(_make_book(1)),
        payment_gateway=gw,
    )
    details = {"card": "4111111111111111"}
    service.process_checkout(1, CART, "1 Main St", "0412345678", details)
    assert gw.charge.call_args[0][1] == details


# ============================================================================
# Total calculation


def test_total_includes_flat_shipping_fee():
    service = _make_service()
    cart = [{"book_id": 1, "quantity": 1, "unit_price": 20.00}]
    order, _ = service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    assert abs(order.total_amount - 29.99) < 0.001


def test_total_sums_all_line_items_plus_shipping():
    service = _make_service(books=[_make_book(1), _make_book(2)])
    cart = [
        {"book_id": 1, "quantity": 2, "unit_price": 10.00},
        {"book_id": 2, "quantity": 1, "unit_price": 5.00},
    ]
    order, _ = service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    assert abs(order.total_amount - 34.99) < 0.001


# ============================================================================
# Order and invoice creation


def test_returns_order_and_invoice():
    order, invoice = _make_service().process_checkout(
        1, CART, "1 Main St", "0412345678", {}
    )
    assert isinstance(order, Order)
    assert isinstance(invoice, Invoice)


def test_order_has_correct_customer_id():
    order, _ = _make_service().process_checkout(42, CART, "1 Main St", "0412345678", {})
    assert order.customer_id == 42


def test_order_has_correct_shipping_address():
    order, _ = _make_service().process_checkout(
        1, CART, "99 Queen St", "0412345678", {}
    )
    assert order.shipping_address == "99 Queen St"


def test_order_has_correct_shipping_phone():
    order, _ = _make_service().process_checkout(1, CART, "1 Main St", "0499999999", {})
    assert order.shipping_phone == "0499999999"


def test_order_has_id_assigned_by_repository():
    service = _make_service(order_id=7)
    order, _ = service.process_checkout(1, CART, "1 Main St", "0412345678", {})
    assert order.order_id == 7


def test_order_items_match_cart():
    service = _make_service()
    cart = [{"book_id": 1, "quantity": 3, "unit_price": 19.99}]
    order, _ = service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    assert len(order.items) == 1
    item = order.items[0]
    assert item.book_id == 1
    assert item.quantity == 3
    assert item.unit_price == 19.99


def test_order_contains_all_cart_items():
    service = _make_service(books=[_make_book(1), _make_book(2)])
    cart = [
        {"book_id": 1, "quantity": 1, "unit_price": 10.00},
        {"book_id": 2, "quantity": 2, "unit_price": 5.00},
    ]
    order, _ = service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    assert len(order.items) == 2


def test_invoice_amount_matches_order_total():
    order, invoice = _make_service().process_checkout(
        1, CART, "1 Main St", "0412345678", {}
    )
    assert invoice.amount_due == order.total_amount


def test_invoice_order_id_matches_saved_order():
    service = _make_service(order_id=5)
    order, invoice = service.process_checkout(1, CART, "1 Main St", "0412345678", {})
    assert invoice.order_id == order.order_id


def test_invoice_has_id_assigned_by_repository():
    service = _make_service(invoice_id=9)
    _, invoice = service.process_checkout(1, CART, "1 Main St", "0412345678", {})
    assert invoice.invoice_id == 9


# ============================================================================
# Stock reduction


def test_stock_reduced_by_quantity_purchased():
    book = _make_book(1, stock=10)
    book_repo = _make_book_repo(book)
    service = CheckoutService(
        order_repo=_make_order_repo(),
        invoice_repo=_make_invoice_repo(),
        book_repo=book_repo,
        payment_gateway=_make_payment_gateway(),
    )
    cart = [{"book_id": 1, "quantity": 3, "unit_price": 19.99}]
    service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    updated = book_repo.update.call_args[0][0]
    assert updated["stock"] == 7


def test_stock_reduced_for_every_item_in_cart():
    book_repo = _make_book_repo(_make_book(1, stock=5), _make_book(2, stock=8))
    service = CheckoutService(
        order_repo=_make_order_repo(),
        invoice_repo=_make_invoice_repo(),
        book_repo=book_repo,
        payment_gateway=_make_payment_gateway(),
    )
    cart = [
        {"book_id": 1, "quantity": 2, "unit_price": 10.00},
        {"book_id": 2, "quantity": 3, "unit_price": 5.00},
    ]
    service.process_checkout(1, cart, "1 Main St", "0412345678", {})
    assert book_repo.update.call_count == 2
