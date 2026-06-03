import re

from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.models.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository


class AuthService:
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_RULES = [
        (r"[A-Z]", "at least one uppercase letter"),
        (r"[a-z]", "at least one lowercase letter"),
        (r"[0-9]", "at least one digit"),
    ]
    EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
    PHONE_PATTERN = r"^[0-9+\-\s\(\)]{7,15}$"

    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

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
        Returns dict of field → error message."""
        errors = {}
        if email and not re.match(self.EMAIL_PATTERN, email):
            errors["email"] = "Enter a valid email address."
        if phone_number and not re.match(self.PHONE_PATTERN, phone_number):
            errors["phone_number"] = "Enter a valid phone number."
        return errors

    def validate(self, email=None, phone_number=None, password=None):
        """Presentation-layer validation: format checks first, then uniqueness.
        Returns dict of field → error message."""
        errors = self._validate_formats(email=email, phone_number=phone_number)

        # Only query DB if format is valid (avoids wasteful lookups)
        if email and "email" not in errors:
            if self.customer_repo.find_by_email(email):
                errors["email"] = "An account with this email already exists."
        if phone_number and "phone_number" not in errors:
            if self.customer_repo.find_by_phone_number(phone_number):
                errors["phone_number"] = "This phone number is already registered."

        pw_errors = self._validate_password(password)
        if pw_errors:
            errors["password"] = "Password must contain " + ", ".join(pw_errors) + "."

        return errors

    def register(
        self, first_name, last_name, email, password, phone_number=None, address=None
    ):
        # Reuse validate() — single source of truth for all checks
        errors = self.validate(
            email=email, phone_number=phone_number, password=password
        )

        # Validate required text fields
        if not first_name or not first_name.strip():
            errors["first_name"] = "First name is required."
        if not last_name or not last_name.strip():
            errors["last_name"] = "Last name is required."

        if errors:
            raise ValueError(", ".join(errors.values()))

        customer = Customer(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=generate_password_hash(password),
            phone_number=phone_number,
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
