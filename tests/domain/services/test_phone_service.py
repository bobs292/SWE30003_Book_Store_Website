from src.domain.services.phone_service import PhoneService


def test_normalize_domestic_unchanged():
    assert PhoneService.normalize_australian_phone("0412345678") == "0412345678"


def test_normalize_plus_international_to_domestic():
    assert PhoneService.normalize_australian_phone("+61412345678") == "0412345678"


def test_normalize_bare_international_to_domestic():
    assert PhoneService.normalize_australian_phone("61412345678") == "0412345678"


def test_normalize_strips_spaces():
    assert PhoneService.normalize_australian_phone("0412 345 678") == "0412345678"


def test_normalize_international_with_spaces():
    assert PhoneService.normalize_australian_phone("+614 12 345 678") == "0412345678"


def test_normalize_none_returns_none():
    assert PhoneService.normalize_australian_phone(None) is None


def test_is_valid_mobile_domestic():
    assert PhoneService.is_valid_australian_mobile("0412345678") is True


def test_is_valid_mobile_plus_international():
    assert PhoneService.is_valid_australian_mobile("+61412345678") is True


def test_is_valid_mobile_rejects_landline():
    assert PhoneService.is_valid_australian_mobile("0312345678") is False


def test_is_valid_mobile_rejects_short():
    assert PhoneService.is_valid_australian_mobile("041234567") is False
