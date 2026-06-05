from datetime import datetime

from src.domain.models.order import Order, OrderItem

# ============================================================================
# OrderItem


def test_order_item_stores_book_id():
    item = OrderItem(book_id=7, quantity=2, unit_price=19.99)
    assert item.book_id == 7


def test_order_item_stores_quantity():
    item = OrderItem(book_id=1, quantity=3, unit_price=9.99)
    assert item.quantity == 3


def test_order_item_stores_unit_price():
    item = OrderItem(book_id=1, quantity=1, unit_price=24.99)
    assert item.unit_price == 24.99


# ============================================================================
# Order — defaults


def test_order_defaults_order_id_to_none():
    assert Order().order_id is None


def test_order_defaults_items_to_empty_list():
    assert Order().items == []


def test_order_items_default_is_independent_per_instance():
    # Each Order must get its own list — a shared mutable default would cause
    # items appended to one order to appear on every other order.
    a = Order()
    b = Order()
    a.items.append(OrderItem(book_id=1, quantity=1, unit_price=1.0))
    assert b.items == []


# ============================================================================
# Order — field storage


def test_order_stores_customer_id():
    assert Order(customer_id=42).customer_id == 42


def test_order_stores_total_amount():
    assert Order(total_amount=49.98).total_amount == 49.98


def test_order_stores_shipping_address():
    assert Order(shipping_address="1 Main St").shipping_address == "1 Main St"


def test_order_stores_shipping_phone():
    assert Order(shipping_phone="0412345678").shipping_phone == "0412345678"


def test_order_stores_order_date():
    now = datetime(2024, 6, 1, 12, 0, 0)
    assert Order(order_date=now).order_date == now


def test_order_stores_items():
    items = [OrderItem(book_id=1, quantity=2, unit_price=19.99)]
    assert Order(items=items).items == items


def test_order_id_can_be_assigned_after_construction():
    # order_id is set by the repository after the row is inserted.
    order = Order(customer_id=1)
    order.order_id = 99
    assert order.order_id == 99
