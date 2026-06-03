import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.gateways.address_gateway import AddressGateway
from src.domain.models.customer import Address, Customer
from src.domain.repositories.customer_repository import CustomerRepository


class AuthService:
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_RULES = [
        (r"[A-Z]", "at least one uppercase letter"),
        (r"[a-z]", "at least one lowercase letter"),
        (r"[0-9]", "at least one digit"),
    ]
    EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    PHONE_PATTERN = re.compile(
        r"^("
        r"\+?614\d{8}"  # International: +614xxxxxxxx or 614xxxxxxxx
        r"|04\d{8}"  # Domestic mobile: 04xxxxxxxx
        r")$"
    )

    def __init__(
        self, customer_repo: CustomerRepository, address_validator: AddressGateway
    ):
        self.customer_repo = customer_repo
        self.address_validator = address_validator

    def _validate_password(self, password):
        """Return list of password requirement error strings. Handles None/empty."""
        if not password:
            return ["a password"]
        errors = []
        if len(password) < self.PASSWORD_MIN_LENGTH:
            errors.append(f"at least {self.PASSWORD_MIN_LENGTH} characters")
        for pattern, message in self.PASSWORD_RULES:
            if not re.search(pattern, password):
                errors.append(message)
        return errors

    def _validate_formats(self, email=None, phone_number=None):
        """Validate format of email and phone without hitting the DB.
        Returns (errors_dict, cleaned_phone)."""
        errors = {}
        cleaned_phone = phone_number
        if email and not re.match(self.EMAIL_PATTERN, email):
            errors["email"] = "Enter a valid email address."
        if phone_number:
            cleaned_phone = phone_number.replace(" ", "")
            if not re.match(self.PHONE_PATTERN, cleaned_phone):
                errors["phone_number"] = "Enter a valid phone number."
        return errors, cleaned_phone

    def _validate_address(self, street=None, suburb=None, state=None, postcode=None):
        # Address is optional — skip the API call when no fields are provided.
        if not any([street, suburb, state, postcode]):
            return None
        return self.address_validator.validate(street, suburb, state, postcode)

    def validate(
        self,
        email=None,
        phone_number=None,
        password=None,
        street=None,
        suburb=None,
        state=None,
        postcode=None,
    ):
        """Validate registration fields. Returns dict of field → error message."""
        errors, cleaned_phone = self._validate_formats(
            email=email, phone_number=phone_number
        )

        if email and "email" not in errors:
            if self.customer_repo.find_by_email(email):
                errors["email"] = "An account with this email already exists."
        if cleaned_phone and "phone_number" not in errors:
            if self.customer_repo.find_by_phone_number(cleaned_phone):
                errors["phone_number"] = "This phone number is already registered."

        pw_errors = self._validate_password(password)
        if pw_errors:
            errors["password"] = "Password must contain " + ", ".join(pw_errors) + "."

        # Validate address via SmartyStreets if any address field was supplied.
        addr_error = self._validate_address(
            street=street, suburb=suburb, state=state, postcode=postcode
        )
        if addr_error:
            errors["address"] = addr_error

        return errors

    def register(
        self,
        first_name,
        last_name,
        email,
        password,
        phone_number=None,
        street=None,
        suburb=None,
        state=None,
        postcode=None,
    ):
        errors = self.validate(
            email=email,
            phone_number=phone_number,
            password=password,
            street=street,
            suburb=suburb,
            state=state,
            postcode=postcode,
        )

        if not first_name or not first_name.strip():
            errors["first_name"] = "First name is required."
        if not last_name or not last_name.strip():
            errors["last_name"] = "Last name is required."

        if errors:
            raise ValueError(", ".join(errors.values()))

        # Normalize phone number — strip spaces before storing.
        cleaned_phone = phone_number.replace(" ", "") if phone_number else None

        # Construct an Address object only when at least one field was provided.
        address = None
        if any([street, suburb, state, postcode]):
            address = Address(
                street=street,
                suburb=suburb,
                state=state,
                postcode=postcode,
            )

        customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password),
            phone_number=cleaned_phone,
            address=address,
        )
        self.customer_repo.save(customer)

    def login(self, email, password):
        customer = self.customer_repo.find_by_email(email)
        if not customer:
            raise ValueError("Invalid email or password.")
        if not check_password_hash(customer.password, password):
            raise ValueError("Invalid email or password.")
        return {"customer_id": customer.customer_id, "email": customer.email}
