import pytest

from src.domain.services.address_validation_service import AddressValidationService


@pytest.fixture
def validator():
    return AddressValidationService()


def test_valid_address_returns_no_errors(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="Melbourne", state="VIC", postcode="3000"
    )
    assert errors == {}


def test_missing_street_returns_error(validator):
    errors = validator.validate_address(
        street="", suburb="Melbourne", state="VIC", postcode="3000"
    )
    assert "street" in errors
    assert errors["street"] == "Street address is required."


def test_missing_suburb_returns_error(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="", state="VIC", postcode="3000"
    )
    assert "suburb" in errors
    assert errors["suburb"] == "Suburb is required."


def test_missing_state_returns_error(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="Melbourne", state="", postcode="3000"
    )
    assert "state" in errors
    assert errors["state"] == "State is required."


def test_invalid_state_format_returns_error(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="Melbourne", state="VICTORIA", postcode="3000"
    )
    assert "state" in errors
    assert "2 or 3 letters" in errors["state"]


def test_valid_state_formats(validator):
    for state in ["VIC", "NSW", "QLD", "WA", "SA", "TAS", "ACT", "NT"]:
        errors = validator.validate_address(
            street="123 Main St", suburb="Melbourne", state=state, postcode="3000"
        )
        assert "state" not in errors


def test_missing_postcode_returns_error(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="Melbourne", state="VIC", postcode=""
    )
    assert "postcode" in errors
    assert errors["postcode"] == "Postcode is required."


def test_invalid_postcode_format_returns_error(validator):
    errors = validator.validate_address(
        street="123 Main St", suburb="Melbourne", state="VIC", postcode="300"
    )
    assert "postcode" in errors
    assert "4 digits" in errors["postcode"]


def test_multiple_errors_returned(validator):
    errors = validator.validate_address(
        street="", suburb="", state="INVALID", postcode="ABC"
    )
    assert "street" in errors
    assert "suburb" in errors
    assert "state" in errors
    assert "postcode" in errors
