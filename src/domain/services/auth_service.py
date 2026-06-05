import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.gateways.address_gateway import AddressGateway
from src.domain.models.customer import Address, Customer
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.services.phone_service import PhoneService


class AuthService:
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_RULES = [
        (r"[A-Z]", "at least one uppercase letter"),
        (r"[a-z]", "at least one lowercase letter"),
        (r"[0-9]", "at least one digit"),
    ]
    EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

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
        Returns (errors_dict, cleaned_phone) where cleaned_phone is normalised."""
        errors = {}
        cleaned_phone = phone_number
        if email and not re.match(self.EMAIL_PATTERN, email):
            errors["email"] = "Enter a valid email address."
        if phone_number:
            cleaned_phone = PhoneService.normalize_australian_phone(phone_number)
            if not PhoneService.is_valid_australian_mobile(cleaned_phone):
                errors["phone_number"] = "Enter a valid phone number."
        return errors, cleaned_phone

    @staticmethod
    def _validate_address_formats(street=None, suburb=None, state=None, postcode=None):
        """Local format checks matching the DB constraints. Returns a dict of
        field → error for any field that fails. Does not hit any external API."""
        errors = {}
        if postcode and not re.fullmatch(r"\d{4}", postcode):
            errors["postcode"] = "Postcode must be exactly 4 digits (e.g. 3000)."
        if state and not re.fullmatch(r"[A-Za-z]{2,3}", state):
            errors["state"] = "State must be 2 or 3 letters (e.g. VIC, NSW)."
        if street and len(street) > 100:
            errors["street"] = "Street address must be 100 characters or fewer."
        if suburb and len(suburb) > 50:
            errors["suburb"] = "Suburb must be 50 characters or fewer."
        return errors

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

        # Local format checks first — skip the API if any format is already wrong.
        addr_format_errors = self._validate_address_formats(
            street=street, suburb=suburb, state=state, postcode=postcode
        )
        errors.update(addr_format_errors)
        if not addr_format_errors:
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

        cleaned_phone = (
            PhoneService.normalize_australian_phone(phone_number)
            if phone_number
            else None
        )

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
        return customer

    def login(self, email, password):
        customer = self.customer_repo.find_by_email(email)
        if not customer:
            raise ValueError("Invalid email or password.")
        if not check_password_hash(customer.password, password):
            raise ValueError("Invalid email or password.")
        return {"customer_id": customer.customer_id, "email": customer.email}
