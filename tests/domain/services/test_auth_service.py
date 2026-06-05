import pytest

from src.domain.gateways.address_gateway import AddressGateway
from src.domain.models.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.services.auth_service import AuthService


# In-memory stub that satisfies the CustomerRepository interface without needing
# a real database. Each test gets a fresh instance via the repo fixture below.
class InMemoryCustomerRepository(CustomerRepository):
    def __init__(self):
        self._store = []

    def save(self, customer):
        self._store.append(customer)

    def find_by_email(self, email):
        return next((c for c in self._store if c.email == email), None)

    def find_by_phone_number(self, phone_number):
        return next((c for c in self._store if c.phone_number == phone_number), None)

    def find_by_id(self, customer_id):
        return next((c for c in self._store if c.customer_id == customer_id), None)


# Stub that satisfies the AddressValidator interface without hitting the network.
# Pass error=None to simulate a valid address; pass an error string to simulate failure.
class StubAddressValidator(AddressGateway):
    def __init__(self, error=None):
        self._error = error

    def validate(self, street, suburb, state, postcode):
        return self._error


# Helper to build a minimal valid Customer for seeding the repo in tests that
# need an existing customer. Override email or phone_number to test uniqueness.
def make_customer(email="default@example.com", phone_number="0411111111"):
    return Customer(
        first_name="Test",
        last_name="User",
        email=email,
        password="hashed",
        phone_number=phone_number,
    )


# Fixtures — pytest injects these into any test function that names them as
# parameters. A fresh repo and service are created for each test, so state
# never leaks between tests.
@pytest.fixture
def repo():
    return InMemoryCustomerRepository()


@pytest.fixture
def service(repo):
    return AuthService(customer_repo=repo, address_validator=StubAddressValidator())


# --- _validate_password ---


def test_validate_password_none_returns_error(service):
    assert service._validate_password(None) == ["a password"]


def test_validate_password_empty_returns_error(service):
    assert service._validate_password("") == ["a password"]


def test_validate_password_too_short(service):
    result = service._validate_password("Ab1")
    assert "at least 8 characters" in result


def test_validate_password_no_uppercase(service):
    result = service._validate_password("password1")
    assert "at least one uppercase letter" in result


def test_validate_password_no_lowercase(service):
    result = service._validate_password("PASSWORD1")
    assert "at least one lowercase letter" in result


def test_validate_password_no_digit(service):
    result = service._validate_password("Password")
    assert "at least one digit" in result


def test_validate_password_multiple_errors(service):
    # A very short, all-lowercase password should trigger multiple rule failures.
    result = service._validate_password("pa")
    assert "at least 8 characters" in result
    assert "at least one uppercase letter" in result
    assert "at least one digit" in result


def test_validate_password_valid_returns_empty(service):
    assert service._validate_password("Passw0rd") == []


# --- _validate_formats ---


def test_validate_formats_valid_email_and_phone(service):
    errors, cleaned = service._validate_formats(
        email="a@b.co", phone_number="0412345678"
    )
    assert errors == {}
    assert cleaned == "0412345678"


def test_validate_formats_invalid_email(service):
    errors, _ = service._validate_formats(email="not-an-email")
    assert errors["email"] == "Enter a valid email address."


def test_validate_formats_invalid_phone(service):
    errors, _ = service._validate_formats(phone_number="12345")
    assert errors["phone_number"] == "Enter a valid phone number."


def test_validate_formats_strips_spaces_from_phone(service):
    # Spaces in phone numbers are stripped before validation.
    errors, cleaned = service._validate_formats(phone_number="0412 345 678")
    assert errors == {}
    assert cleaned == "0412345678"


def test_validate_formats_international_phone_with_plus(service):
    # +61XXXXXXXXX is valid and normalised to domestic 0XXXXXXXXX.
    errors, cleaned = service._validate_formats(phone_number="+61412345678")
    assert errors == {}
    assert cleaned == "0412345678"


def test_validate_formats_international_phone_without_plus(service):
    # 61XXXXXXXXX (no leading +) is valid and normalised to 0XXXXXXXXX.
    errors, cleaned = service._validate_formats(phone_number="61412345678")
    assert errors == {}
    assert cleaned == "0412345678"


def test_validate_formats_none_email_and_phone(service):
    # Both fields are optional; omitting them should produce no errors.
    errors, cleaned = service._validate_formats(email=None, phone_number=None)
    assert errors == {}
    assert cleaned is None


# --- _normalize_phone ---


def test_normalize_phone_domestic_unchanged(service):
    assert service._normalize_phone("0412345678") == "0412345678"


def test_normalize_phone_plus_international_to_domestic(service):
    assert service._normalize_phone("+61412345678") == "0412345678"


def test_normalize_phone_bare_international_to_domestic(service):
    assert service._normalize_phone("61412345678") == "0412345678"


def test_normalize_phone_strips_spaces(service):
    assert service._normalize_phone("0412 345 678") == "0412345678"


def test_normalize_phone_international_with_spaces(service):
    assert service._normalize_phone("+614 12 345 678") == "0412345678"


def test_normalize_phone_none_returns_none(service):
    assert service._normalize_phone(None) is None


# --- validate ---


def test_validate_all_valid_returns_empty(service, repo):
    repo.save(make_customer())
    errors = service.validate(
        email="new@example.com", phone_number="0499999999", password="Passw0rd"
    )
    assert errors == {}


def test_validate_duplicate_email(service, repo):
    repo.save(make_customer(email="taken@example.com"))
    errors = service.validate(
        email="taken@example.com", phone_number="0499999999", password="Passw0rd"
    )
    assert errors["email"] == "An account with this email already exists."


def test_validate_duplicate_phone(service, repo):
    repo.save(make_customer(phone_number="0412345678"))
    errors = service.validate(
        email="new@example.com", phone_number="0412345678", password="Passw0rd"
    )
    assert errors["phone_number"] == "This phone number is already registered."


def test_validate_duplicate_phone_cross_format(service, repo):
    # A number registered as +61XXXXXXXXX must block re-registration as
    # 0XXXXXXXXX (and vice-versa) because both normalise to the same value.
    repo.save(make_customer(phone_number="0412345678"))
    errors = service.validate(
        email="new@example.com", phone_number="+61412345678", password="Passw0rd"
    )
    assert errors["phone_number"] == "This phone number is already registered."


def test_validate_skips_uniqueness_if_format_invalid(service, repo):
    # If the email format is bad, the DB should not be queried for uniqueness.
    errors = service.validate(
        email="bad-email", phone_number="0499999999", password="Passw0rd"
    )
    assert "email" in errors
    assert "already exists" not in errors["email"]


def test_validate_password_errors_included(service):
    # Password errors should be surfaced through validate(),
    # not just _validate_password().
    errors = service.validate(email="a@b.co", password="short")
    assert "password" in errors
    assert "at least 8 characters" in errors["password"]


# --- register ---


def test_register_missing_first_name_raises(service, repo):
    with pytest.raises(ValueError, match="First name is required"):
        service.register("", "Smith", "a@b.co", "Passw0rd")


def test_register_missing_last_name_raises(service, repo):
    with pytest.raises(ValueError, match="Last name is required"):
        service.register("John", "", "a@b.co", "Passw0rd")


def test_register_whitespace_first_name_raises(service, repo):
    with pytest.raises(ValueError, match="First name is required"):
        service.register("   ", "Smith", "a@b.co", "Passw0rd")


def test_register_whitespace_last_name_raises(service, repo):
    with pytest.raises(ValueError, match="Last name is required"):
        service.register("John", "   ", "a@b.co", "Passw0rd")


def test_register_strips_spaces_from_phone(service, repo):
    # Phone numbers with spaces should be normalised before being stored.
    service.register("John", "Smith", "a@b.co", "Passw0rd", phone_number="0412 345 678")
    customer = repo.find_by_phone_number("0412345678")
    assert customer is not None


def test_register_duplicate_email_raises(service, repo):
    service.register("John", "Smith", "taken@b.co", "Passw0rd")
    with pytest.raises(ValueError, match="already exists"):
        service.register("Jane", "Doe", "taken@b.co", "Passw0rd1")


def test_register_duplicate_phone_raises(service, repo):
    service.register("John", "Smith", "a@b.co", "Passw0rd", phone_number="0412345678")
    with pytest.raises(ValueError, match="already registered"):
        service.register(
            "Jane", "Doe", "c@d.co", "Passw0rd1", phone_number="0412345678"
        )


def test_register_duplicate_phone_cross_format_raises(service, repo):
    # Registering with +61XXXXXXXXX then 0XXXXXXXXX (or vice-versa) must be
    # rejected because both normalise to the same stored value.
    service.register("John", "Smith", "a@b.co", "Passw0rd", phone_number="0412345678")
    with pytest.raises(ValueError, match="already registered"):
        service.register(
            "Jane", "Doe", "c@d.co", "Passw0rd1", phone_number="+61412345678"
        )


def test_register_invalid_password_raises(service, repo):
    with pytest.raises(ValueError, match="Password must contain"):
        service.register("John", "Smith", "a@b.co", "short")


# --- _validate_address_formats ---


def test_validate_address_formats_valid_returns_empty(service):
    assert (
        service._validate_address_formats(
            street="1 Main St", suburb="Melbourne", state="VIC", postcode="3000"
        )
        == {}
    )


def test_validate_address_formats_postcode_too_long(service):
    errors = service._validate_address_formats(postcode="301667")
    assert "postcode" in errors


def test_validate_address_formats_postcode_too_short(service):
    errors = service._validate_address_formats(postcode="300")
    assert "postcode" in errors


def test_validate_address_formats_postcode_non_digits(service):
    errors = service._validate_address_formats(postcode="3OOO")
    assert "postcode" in errors


def test_validate_address_formats_state_too_long(service):
    errors = service._validate_address_formats(state="VICTORIA")
    assert "state" in errors


def test_validate_address_formats_state_non_letters(service):
    errors = service._validate_address_formats(state="V1")
    assert "state" in errors


def test_validate_address_formats_street_over_limit(service):
    errors = service._validate_address_formats(street="A" * 101)
    assert "street" in errors


def test_validate_address_formats_suburb_over_limit(service):
    errors = service._validate_address_formats(suburb="A" * 51)
    assert "suburb" in errors


def test_validate_address_formats_none_fields_returns_empty(service):
    assert service._validate_address_formats() == {}


# --- validate — address format integration ---


def test_validate_returns_postcode_error_for_invalid_postcode(service):
    errors = service.validate(email="a@b.co", password="Passw0rd", postcode="301667")
    assert "postcode" in errors


def test_validate_returns_state_error_for_invalid_state(service):
    errors = service.validate(email="a@b.co", password="Passw0rd", state="VICTORIA")
    assert "state" in errors


def test_validate_skips_smartystreets_when_address_format_invalid(repo):
    # SmartyStreets must not be called when a local format check already failed.
    from unittest.mock import MagicMock

    spy = MagicMock()
    spy.validate.return_value = None
    svc = AuthService(customer_repo=repo, address_validator=spy)
    svc.validate(
        email="a@b.co",
        password="Passw0rd",
        street="1 Main St",
        suburb="Melbourne",
        state="VICTORIA",
        postcode="3000",
    )
    spy.validate.assert_not_called()


# --- _validate_address ---


@pytest.fixture
def valid_address_validator():
    return StubAddressValidator(error=None)


@pytest.fixture
def invalid_address_validator():
    return StubAddressValidator(error="Address could not be verified.")


@pytest.fixture
def service_with_address_validator(repo, valid_address_validator):
    return AuthService(customer_repo=repo, address_validator=valid_address_validator)


def test_validate_address_no_fields_skips_validator(
    service_with_address_validator,
):
    assert service_with_address_validator._validate_address() is None


def test_validate_address_valid_returns_none(service_with_address_validator):
    result = service_with_address_validator._validate_address(
        street="1 Main St", suburb="Melbourne", state="VIC", postcode="3000"
    )
    assert result is None


def test_validate_address_invalid_returns_error(repo, invalid_address_validator):
    svc = AuthService(customer_repo=repo, address_validator=invalid_address_validator)
    result = svc._validate_address(
        street="99 Fake St", suburb="Nowhere", state="VIC", postcode="9999"
    )
    assert result == "Address could not be verified."


def test_validate_includes_address_error(repo, invalid_address_validator):
    svc = AuthService(customer_repo=repo, address_validator=invalid_address_validator)
    errors = svc.validate(
        email="a@b.co",
        password="Passw0rd",
        street="99 Fake St",
        suburb="Nowhere",
        state="VIC",
        postcode="9999",
    )
    assert errors["address"] == "Address could not be verified."


def test_validate_no_address_error_when_valid(repo, valid_address_validator):
    svc = AuthService(customer_repo=repo, address_validator=valid_address_validator)
    errors = svc.validate(
        email="a@b.co",
        password="Passw0rd",
        street="1 Main St",
        suburb="Melbourne",
        state="VIC",
        postcode="3000",
    )
    assert "address" not in errors


def test_register_builds_address_object(repo, valid_address_validator):
    svc = AuthService(customer_repo=repo, address_validator=valid_address_validator)
    svc.register(
        "John",
        "Smith",
        "a@b.co",
        "Passw0rd",
        street="1 Main St",
        suburb="Melbourne",
        state="VIC",
        postcode="3000",
    )
    customer = repo.find_by_email("a@b.co")
    assert customer.address is not None
    assert customer.address.street == "1 Main St"
    assert customer.address.suburb == "Melbourne"
    assert customer.address.state == "VIC"
    assert customer.address.postcode == "3000"


def test_register_no_address_fields_leaves_address_none(repo):
    svc = AuthService(customer_repo=repo, address_validator=StubAddressValidator())
    svc.register("John", "Smith", "a@b.co", "Passw0rd")
    customer = repo.find_by_email("a@b.co")
    assert customer.address is None


def test_register_invalid_address_raises(repo, invalid_address_validator):
    svc = AuthService(customer_repo=repo, address_validator=invalid_address_validator)
    with pytest.raises(ValueError, match="Address could not be verified"):
        svc.register(
            "John",
            "Smith",
            "a@b.co",
            "Passw0rd",
            street="99 Fake St",
            suburb="Nowhere",
            state="VIC",
            postcode="9999",
        )
