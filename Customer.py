from User import User
class Customer(User): 
    def __init__(self,name, address, phone_number, password):
        super().__init__(name, address, phone_number, password)

    