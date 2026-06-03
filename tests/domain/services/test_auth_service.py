import pytest

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
    return AuthService(customer_repo=repo)


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


def test_validate_formats_international_phone(service):
    errors, cleaned = service._validate_formats(phone_number="+61412345678")
    assert errors == {}
    assert cleaned == "+61412345678"


def test_validate_formats_none_email_and_phone(service):
    # Both fields are optional; omitting them should produce no errors.
    errors, cleaned = service._validate_formats(email=None, phone_number=None)
    assert errors == {}
    assert cleaned is None


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


def test_register_invalid_password_raises(service, repo):
    with pytest.raises(ValueError, match="Password must contain"):
        service.register("John", "Smith", "a@b.co", "short")
