import json
import phonenumbers
import string
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data.json"

class User:
    def __init__(self, username,name, address, phone_number, password, admin=False):
        self.username = str(username)
        self.name = str(name)
        self.address = str(address)
        self.phone_number = str(phone_number)
        self.password = str(password)
        self.admin = admin

    def to_dict(self):
        return {self.username: {
            "name": self.name,
            "address": self.address,
            "phone_number": self.phone_number,
            "password": self.password,
            "admin": self.admin,
        }
        }

    def create_user(self):
        users = self.to_dict()
        print(users)
        with open(DATA_FILE, "w") as file:
            json.dump(users, file, indent=4)

    @classmethod
    def _load_users(cls):
        if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
            return []
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            return []
