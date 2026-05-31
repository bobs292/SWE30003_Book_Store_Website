from src.data.database import get_connection
from src.domain.models.customer import Address, Customer
from src.domain.repositories.customer_repository import CustomerRepository


class SqliteCustomerRepository(CustomerRepository):

    def save(self, customer):
        conn = get_connection()
        cursor = conn.cursor()
        # Flatten the Address object into four columns for storage.
        street = customer.address.street if customer.address else None
        suburb = customer.address.suburb if customer.address else None
        state = customer.address.state if customer.address else None
        postcode = customer.address.postcode if customer.address else None
        cursor.execute(
            """INSERT INTO customers
               (first_name, last_name, email, phone_number,
                password, street, suburb, state, postcode)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                customer.first_name,
                customer.last_name,
                customer.email,
                customer.phone_number,
                customer.password,
                street,
                suburb,
                state,
                postcode,
            ),
        )
        conn.commit()
        conn.close()

    def _row_to_customer(self, row):
        # Reconstruct the Address object from the four database columns if present.
        address = None
        if row["street"] is not None:
            address = Address(
                street=row["street"],
                suburb=row["suburb"],
                state=row["state"],
                postcode=row["postcode"],
            )
        return Customer(
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            password=row["password"],
            phone_number=row["phone_number"],
            address=address,
            customer_id=row["customer_id"],
        )

    def find_by_email(self, email):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_customer(row)

    def find_by_id(self, customer_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE customer_id = ?", (customer_id,))
        row = cursor.fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_customer(row)
