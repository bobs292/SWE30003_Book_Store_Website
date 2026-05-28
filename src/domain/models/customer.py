from src.domain.models.user import User

# Represents a customer's delivery address as a single unit.
# All four fields are required. It is impossible to create a partial address.
class Address:
    def __init__(self, street, suburb, state, postcode):
        self.street = street
        self.suburb = suburb
        self.state = state
        self.postcode = postcode

# Concrete subclass of User representing a purchasing actor.
class Customer(User):
    # phone_number and address default to None making them optional.
    # customer_id defaults to None as it is assigned by the database on save.
    def __init__(self, first_name, last_name, email, password, phone_number=None, address=None, customer_id=None):
        # Calls the User constructor to set first_name, last_name, email and password.
        # Without this the Customer object would not have those attributes.
        super().__init__(first_name, last_name, email, password)
        self.phone_number = phone_number
        self.address = address  # None or an Address object
        self.customer_id = customer_id