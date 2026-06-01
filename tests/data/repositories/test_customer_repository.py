import sqlite3

import pytest

import src.data.database as db_module
from src.data.database import init_db
from src.data.repositories.customer_repository import SqliteCustomerRepository
from src.domain.models.customer import Address, Customer


@pytest.fixture(autouse=True)
def _setup_db(monkeypatch, tmp_path):
    db_file = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))
    init_db()


@pytest.fixture
def repo():
    return SqliteCustomerRepository()


VALID_PASSWORD = "$2b$12$ahashedpasswordthatisatleast60characterslong1234567890ab"
VALID_ADDRESS = Address(
    street="1 Example Street", suburb="Melbourne", state="VIC", postcode="3000"
)


def make_customer(**overrides):
    defaults = dict(
        first_name="John",
        last_name="Smith",
        email="john.smith@example.com",
        phone_number="0412345678",
        password=VALID_PASSWORD,
        address=None,
    )
    defaults.update(overrides)
    return Customer(**defaults)


def test_first_name_lower_bound(repo):
    repo.save(make_customer(first_name="J"))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_first_name_upper_bound(repo):
    repo.save(make_customer(first_name="J" * 35))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_first_name_empty_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(first_name=""))


def test_first_name_over_limit_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(first_name="J" * 36))


def test_last_name_lower_bound(repo):
    repo.save(make_customer(last_name="S"))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_last_name_upper_bound(repo):
    repo.save(make_customer(last_name="S" * 35))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_last_name_empty_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(last_name=""))


def test_last_name_over_limit_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(last_name="S" * 36))


def test_email_lower_bound(repo):
    repo.save(make_customer(email="a@b.co"))
    assert repo.find_by_email("a@b.co") is not None


def test_email_upper_bound(repo):
    email = "a" * 242 + "@example.com"
    repo.save(make_customer(email=email))
    assert repo.find_by_email(email) is not None


def test_email_no_at_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(email="ab.co12"))


def test_email_with_space_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(email="a @b.co"))


def test_email_too_short_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(email="a@b.c"))


def test_email_over_limit_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(email="a" * 244 + "@example.com"))


def test_email_must_be_unique(repo):
    repo.save(make_customer(email="john.smith@example.com"))
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(email="john.smith@example.com"))


def test_phone_number_null_is_valid(repo):
    repo.save(make_customer(phone_number=None))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_phone_number_lower_bound(repo):
    repo.save(make_customer(phone_number="0412345678"))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_phone_number_upper_bound(repo):
    repo.save(make_customer(phone_number="041234567890123"))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_phone_number_too_short_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(phone_number="041234567"))


def test_phone_number_too_long_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(phone_number="0412345678901234"))


def test_phone_number_non_digits_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(phone_number="041234abc8"))


def test_password_lower_bound(repo):
    repo.save(make_customer(password="a" * 60))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_password_too_short_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(make_customer(password="a" * 59))


def test_full_address_is_valid(repo):
    repo.save(make_customer(address=VALID_ADDRESS))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_no_address_is_valid(repo):
    repo.save(make_customer(address=None))
    assert repo.find_by_email("john.smith@example.com") is not None


def test_street_lower_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="A", suburb="Melbourne", state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_street_upper_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="A" * 100, suburb="Melbourne", state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_street_over_limit_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="A" * 101, suburb="Melbourne", state="VIC", postcode="3000"
                )
            )
        )


def test_suburb_lower_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="1 Example St", suburb="A", state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_suburb_upper_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="1 Example St", suburb="A" * 50, state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_suburb_over_limit_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St", suburb="A" * 51, state="VIC", postcode="3000"
                )
            )
        )


def test_state_lower_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="1 Example St", suburb="Melbourne", state="VI", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_state_upper_bound(repo):
    repo.save(
        make_customer(
            address=Address(
                street="1 Example St", suburb="Melbourne", state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_state_too_short_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="V",
                    postcode="3000",
                )
            )
        )


def test_state_too_long_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="VICT",
                    postcode="3000",
                )
            )
        )


def test_state_non_letters_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="V1",
                    postcode="3000",
                )
            )
        )


def test_postcode_valid(repo):
    repo.save(
        make_customer(
            address=Address(
                street="1 Example St", suburb="Melbourne", state="VIC", postcode="3000"
            )
        )
    )
    assert repo.find_by_email("john.smith@example.com") is not None


def test_postcode_too_short_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="VIC",
                    postcode="300",
                )
            )
        )


def test_postcode_too_long_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="VIC",
                    postcode="30001",
                )
            )
        )


def test_postcode_non_digits_raises(repo):
    with pytest.raises(sqlite3.IntegrityError):
        repo.save(
            make_customer(
                address=Address(
                    street="1 Example St",
                    suburb="Melbourne",
                    state="VIC",
                    postcode="3O0O",
                )
            )
        )
