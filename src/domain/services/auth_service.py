from werkzeug.security import check_password_hash, generate_password_hash

from src.domain.models.customer import Customer
from src.domain.repositories.customer_repository import CustomerRepository


class AuthService:
    def __init__(self, customer_repo: CustomerRepository):
        self.customer_repo = customer_repo

    def register(
        self, first_name, last_name, email, password, phone_number=None, address=None
    ):
        if self.customer_repo.find_by_email(email):
            raise ValueError("An account with this email already exists.")
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
