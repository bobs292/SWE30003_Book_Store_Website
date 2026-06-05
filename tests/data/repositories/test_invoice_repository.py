from datetime import datetime

import pytest

import src.data.database as db_module
from src.data.database import init_db
from src.data.repositories.invoice_repository import SqliteInvoiceRepository
from src.data.repositories.order_repository import SqliteOrderRepository
from src.domain.models.invoice import Invoice
from src.domain.models.order import Order


@pytest.fixture(autouse=True)
def _setup_db(monkeypatch, tmp_path):
    monkeypatch.setattr(db_module, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(db_module, "SEEDS_PATH", str(tmp_path / "data.json"))
    init_db()


@pytest.fixture
def repo():
    return SqliteInvoiceRepository()


@pytest.fixture
def saved_order_id():
    # Invoices have a NOT NULL FK to orders. Create a real order first.
    order_repo = SqliteOrderRepository()
    order = Order(
        customer_id=1,
        order_date=datetime(2024, 6, 1, 12, 0, 0),
        total_amount=29.99,
        shipping_address="1 Main St",
        shipping_phone="0412345678",
    )
    saved = order_repo.save(order)
    return saved.order_id


INVOICE_DATE = datetime(2024, 6, 1, 12, 0, 1)


def _make_invoice(order_id, **overrides):
    defaults = dict(
        order_id=order_id,
        invoice_date=INVOICE_DATE,
        amount_due=29.99,
    )
    defaults.update(overrides)
    return Invoice(**defaults)


# ============================================================================
# save


def test_save_returns_invoice_with_id_assigned(repo, saved_order_id):
    invoice = repo.save(_make_invoice(saved_order_id))
    assert invoice.invoice_id is not None
    assert isinstance(invoice.invoice_id, int)


def test_save_assigns_different_ids_to_different_invoices(repo, saved_order_id):
    a = repo.save(_make_invoice(saved_order_id))
    b = repo.save(_make_invoice(saved_order_id))
    assert a.invoice_id != b.invoice_id


def test_save_persists_order_id(repo, saved_order_id):
    invoice = repo.save(_make_invoice(saved_order_id))
    assert invoice.order_id == saved_order_id


def test_save_persists_amount_due(repo, saved_order_id):
    invoice = repo.save(_make_invoice(saved_order_id, amount_due=59.98))
    assert abs(invoice.amount_due - 59.98) < 0.001


def test_save_mutates_invoice_id_in_place(repo, saved_order_id):
    # The repository sets invoice.invoice_id directly on the passed object.
    invoice = _make_invoice(saved_order_id)
    assert invoice.invoice_id is None
    repo.save(invoice)
    assert invoice.invoice_id is not None
