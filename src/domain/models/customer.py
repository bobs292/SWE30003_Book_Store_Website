from src.domain.models.user import User

class Customer(User):
    def __init__(self, first_name, last_name, email, password, phone_number=None, street=None, suburb=None, state=None, postcode=None, customer_id=None):
        super().__init__(first_name, last_name, email, password)
        self.phone_number = phone_number
        self.street = street
        self.suburb = suburb
        self.state = state
        self.postcode = postcode
        self.customer_id = customer_id
