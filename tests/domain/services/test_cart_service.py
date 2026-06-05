import pytest

from src.domain.services.cart_service import CartService

BOOKS = [
    {"id": 1, "title": "The Hobbit", "price": 19.99, "stock": 5},
    {"id": 2, "title": "Dune", "price": 24.99, "stock": 3},
]


class TestSafeInt:
    def test_valid_int_string(self):
        assert CartService.safe_int("42") == 42

    def test_invalid_int_string_returns_default(self):
        assert CartService.safe_int("abc") == 0
        assert CartService.safe_int("abc", 10) == 10

    def test_none_returns_default(self):
        assert CartService.safe_int(None) == 0
        assert CartService.safe_int(None, 5) == 5

    def test_float_string_returns_truncated(self):
        assert CartService.safe_int("3.14") == 0  # Conversion fails


class TestSafeFloat:
    def test_valid_float_string(self):
        assert CartService.safe_float("19.99") == 19.99

    def test_valid_int_string(self):
        assert CartService.safe_float("42") == 42.0

    def test_invalid_float_string_returns_default(self):
        assert CartService.safe_float("abc") == 0.0
        assert CartService.safe_float("abc", 9.99) == 9.99

    def test_none_returns_default(self):
        assert CartService.safe_float(None) == 0.0
        assert CartService.safe_float(None, 5.5) == 5.5


class TestNormalizeCart:
    def test_empty_dict_returns_empty_dict(self):
        assert CartService.normalize_cart({}) == {}

    def test_converts_string_keys_to_string(self):
        cart = {1: "2", 2: "3"}
        result = CartService.normalize_cart(cart)
        assert result == {"1": 2, "2": 3}

    def test_invalid_values_coerced_to_zero(self):
        cart = {"1": "abc", "2": None, "3": "5"}
        result = CartService.normalize_cart(cart)
        assert result == {"1": 0, "2": 0, "3": 5}

    def test_non_dict_returns_empty_dict(self):
        assert CartService.normalize_cart(None) == {}
        assert CartService.normalize_cart("invalid") == {}
        assert CartService.normalize_cart([1, 2, 3]) == {}


class TestBuildCartItems:
    def test_valid_cart_builds_items_with_subtotal(self):
        cart = {"1": 2, "2": 1}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert len(items) == 2
        assert items[0]["quantity"] == 2
        assert items[0]["line_total"] == 19.99 * 2
        assert items[1]["quantity"] == 1
        assert items[1]["line_total"] == 24.99
        assert subtotal == pytest.approx(19.99 * 2 + 24.99)
        assert not changed

    def test_removes_item_not_in_catalogue(self):
        cart = {"1": 1, "999": 2}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert len(items) == 1
        assert "999" not in cart
        assert changed

    def test_removes_zero_quantity_items(self):
        cart = {"1": 1, "2": 0}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert len(items) == 1
        assert "2" not in cart
        assert changed

    def test_empty_cart_returns_no_items(self):
        cart = {}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert items == []
        assert subtotal == 0.0
        assert not changed

    def test_cart_with_all_removed_items_becomes_empty(self):
        cart = {"999": 1, "888": 2}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert items == []
        assert cart == {}
        assert changed

    def test_negative_quantities_treated_as_zero(self):
        cart = {"1": -5}
        items, subtotal, changed = CartService.build_cart_items(BOOKS, cart)

        assert items == []
        assert changed
