from datetime import datetime

from src.domain.models.invoice import Invoice

# ============================================================================
# Invoice — defaults


def test_invoice_defaults_invoice_id_to_none():
    assert Invoice().invoice_id is None


def test_invoice_defaults_order_id_to_none():
    assert Invoice().order_id is None


def test_invoice_defaults_invoice_date_to_none():
    assert Invoice().invoice_date is None


def test_invoice_defaults_amount_due_to_none():
    assert Invoice().amount_due is None


# ============================================================================
# Invoice — field storage


def test_invoice_stores_order_id():
    assert Invoice(order_id=5).order_id == 5


def test_invoice_stores_amount_due():
    assert Invoice(amount_due=59.97).amount_due == 59.97


def test_invoice_stores_invoice_date():
    now = datetime(2024, 6, 1, 10, 0, 0)
    assert Invoice(invoice_date=now).invoice_date == now


def test_invoice_id_can_be_assigned_after_construction():
    # invoice_id is set by the repository after the row is inserted.
    invoice = Invoice(order_id=3, amount_due=29.99)
    invoice.invoice_id = 101
    assert invoice.invoice_id == 101
