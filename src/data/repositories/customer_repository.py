import sqlite3
from src.domain.repositories.customer_repository import CustomerRepository
from src.domain.models.customer import Customer
from src.data.database import get_connection


class SqliteCustomerRepository(CustomerRepository):

    def save(self, customer):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO customers
            (first_name, last_name, email, phone_number, password, street, suburb, state, postcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (customer.first_name, customer.last_name, customer.email, customer.phone_number,
             customer.password, customer.street, customer.suburb, customer.state, customer.postcode)
        )
        conn.commit()
        conn.close()

    def find_by_email(self, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return Customer(
            first_name=row["first_name"], last_name=row["last_name"], email=row["email"],
            password=row["password"], phone_number=row["phone_number"], street=row["street"],
            suburb=row["suburb"], state=row["state"], postcode=row["postcode"],
            customer_id=row["customer_id"]
        )

    def find_by_id(self, customer_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return Customer(
            first_name=row["first_name"], last_name=row["last_name"], email=row["email"],
            password=row["password"], phone_number=row["phone_number"], street=row["street"],
            suburb=row["suburb"], state=row["state"], postcode=row["postcode"],
            customer_id=row["customer_id"]
        )
