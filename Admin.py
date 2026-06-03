import json
import User
class Admin(User): 
    def __init__(self):
        self.name = "Admin"
        self.address = "address" 
        self.phone_number = "000"
        self.password = "password"
    
    def dict(self):
        return {
            "name":  self.name,
            "address":  self.address,
            "phone_number":  self.phone_number,
            "admin": True,
            "password": self.password
        }
        