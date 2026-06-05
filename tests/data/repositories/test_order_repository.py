from datetime import datetime

import pytest

import src.data.database as db_module
from src.data.database import init_db
from src.data.repositories.order_repository import SqliteOrderRepository
from src.domain.models.order import Order, OrderItem


@pytest.fixture(autouse=True)
def _setup_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(db_module, "SEEDS_PATH", str(tmp_path / "data.json"))
    init_db()


@pytest.fixture
def repo():
    return SqliteOrderRepository()


ORDER_DATE = datetime(2024, 6, 1, 12, 0, 0)

ITEMS = [
    OrderItem(book_id=1, quantity=2, unit_price=19.99),
    OrderItem(book_id=2, quantity=1, unit_price=24.99),
]


def _make_order(**overrides):
    defaults = dict(
        customer_id=1,
        order_date=ORDER_DATE,
        total_amount=74.97,
        shipping_address="1 Main St, Melbourne VIC 3000",
        shipping_phone="0412345678",
        items=list(ITEMS),
    )
    defaults.update(overrides)
    return Order(**defaults)


# ============================================================================
# save


def test_save_returns_order_with_id_assigned(repo):
    order = repo.save(_make_order())
    assert order.order_id is not None
    assert isinstance(order.order_id, int)


def test_save_assigns_different_ids_to_different_orders(repo):
    a = repo.save(_make_order())
    b = repo.save(_make_order())
    assert a.order_id != b.order_id


def test_save_persists_customer_id(repo):
    order = repo.save(_make_order(customer_id=99))
    fetched = repo.find_by_id(order.order_id)
    assert fetched.customer_id == 99


def test_save_persists_total_amount(repo):
    order = repo.save(_make_order(total_amount=49.98))
    fetched = repo.find_by_id(order.order_id)
    assert abs(fetched.total_amount - 49.98) < 0.001


def test_save_persists_shipping_address(repo):
    order = repo.save(_make_order(shipping_address="99 Queen St"))
    fetched = repo.find_by_id(order.order_id)
    assert fetched.shipping_address == "99 Queen St"


def test_save_persists_shipping_phone(repo):
    order = repo.save(_make_order(shipping_phone="0499999999"))
    fetched = repo.find_by_id(order.order_id)
    assert fetched.shipping_phone == "0499999999"


def test_save_persists_order_date(repo):
    order = repo.save(_make_order(order_date=ORDER_DATE))
    fetched = repo.find_by_id(order.order_id)
    assert fetched.order_date == ORDER_DATE


def test_save_persists_all_order_items(repo):
    order = repo.save(_make_order())
    fetched = repo.find_by_id(order.order_id)
    assert len(fetched.items) == 2


def test_save_persists_item_book_id(repo):
    order = repo.save(
        _make_order(items=[OrderItem(book_id=7, quantity=1, unit_price=9.99)])
    )
    fetched = repo.find_by_id(order.order_id)
    assert fetched.items[0].book_id == 7


def test_save_persists_item_quantity(repo):
    order = repo.save(
        _make_order(items=[OrderItem(book_id=1, quantity=5, unit_price=9.99)])
    )
    fetched = repo.find_by_id(order.order_id)
    assert fetched.items[0].quantity == 5


def test_save_persists_item_unit_price(repo):
    order = repo.save(
        _make_order(items=[OrderItem(book_id=1, quantity=1, unit_price=24.99)])
    )
    fetched = repo.find_by_id(order.order_id)
    assert abs(fetched.items[0].unit_price - 24.99) < 0.001


def test_save_order_with_no_items(repo):
    order = repo.save(_make_order(items=[]))
    fetched = repo.find_by_id(order.order_id)
    assert fetched.items == []


# ============================================================================
# find_by_id


def test_find_by_id_returns_none_for_missing_order(repo):
    assert repo.find_by_id(9999) is None


def test_find_by_id_returns_order(repo):
    order = repo.save(_make_order())
    fetched = repo.find_by_id(order.order_id)
    assert fetched is not None
    assert fetched.order_id == order.order_id


def test_find_by_id_reconstructs_items_as_order_item_objects(repo):
    order = repo.save(_make_order())
    fetched = repo.find_by_id(order.order_id)
    assert all(isinstance(item, OrderItem) for item in fetched.items)


def test_find_by_id_reconstructs_datetime(repo):
    order = repo.save(_make_order(order_date=ORDER_DATE))
    fetched = repo.find_by_id(order.order_id)
    assert isinstance(fetched.order_date, datetime)
    assert fetched.order_date == ORDER_DATE
