import json
import os
import string

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from email_validator import validate_email, EmailNotValidError
from smartystreets_python_sdk import BasicAuthCredentials, ClientBuilder
from smartystreets_python_sdk.international_street import Lookup as InternationalLookup
import phonenumbers

DATA_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "seeds", "data.json")
)

# DON'T DO THIS!!!!
Auth_id = "02a657c9-a194-cb5d-8a4a-69bc63bf2367"
Auth_token = "GLc5gzDJ5MpDKHwuSPdo"

def create_auth_routes(auth_service):
    
    def check_email(email):
        try:
            validate_email(email)
            return None
        except EmailNotValidError as e:
            return str(e)
 
    def check_password(password):
        if len(password) >= 12 and any(char in string.punctuation for char in password):
            return None
        return "Password must be 12 or more characters and include at least 1 special character"
 
    def check_phone_number(number_string, country_code="AU"):
        if not number_string:
            return None  # phone is optional — skip validation if blank
        try:
            parsed_number = phonenumbers.parse(number_string, country_code)
            is_possible = phonenumbers.is_possible_number(parsed_number)
            is_valid = phonenumbers.is_valid_number(parsed_number)
 
            if is_valid:
                return None
            elif is_possible:
                return "Possible but invalid format or non-existent prefix"
            else:
                return "Invalid number"
        except phonenumbers.NumberParseException:
            return "Invalid format (cannot parse)"
 
    def address_check(address):
        credentials = BasicAuthCredentials(Auth_id, Auth_token)
        client = ClientBuilder(credentials).build_international_street_api_client()
        lookup = InternationalLookup()
        lookup.country = "Australia"
        lookup.address1 = address
        try:
            result = client.send(lookup)
            if hasattr(result, "result") and result.result:
                return None
            if isinstance(result, list) and len(result) > 0:
                return None
            return "Address could not be verified"
        except Exception as e:
            return str(e)
 
    def test_user(first_name, last_name, address, email, password, phone_number):
        if not first_name or not last_name or not address or not email or not password:
            return "All required fields must be filled in."
        if len(first_name) <= 3:
            return "First name must have more than 3 characters"
        if len(last_name) <= 3:
            return "Last name must have more than 3 characters"
 
        err = check_email(email)
        if err:
            return err
 
        err = check_phone_number(phone_number)
        if err:
            return err
 
        err = check_password(password)
        if err:
            return err
 
        err = address_check(address)
        if err:
            return err
 
        if auth_service.customer_repo.find_by_email(email):
            return "An account with that email already exists"
 
        return None
    
    auth = Blueprint("auth", __name__)

    @auth.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            email = request.form.get("email")
            address = request.form.get("address")
            password = request.form.get("password")
            phone_number = request.form.get("phone_number")

            err = test_user(first_name, last_name, address, email, password, phone_number)
            if err:
                flash(err, "error")
                return render_template("register.html")
 
            try:
                user = auth_service.register(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    address=address,
                    password=password,
                    phone_number=phone_number or None,
                )

                # Persist a copy of the registered user in the JSON users list.
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as data_file:
                        data = json.load(data_file)
                except FileNotFoundError:
                    data = {}

                data.setdefault("users", [])
                data["users"].append(
                    {
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "email": user.email,
                        "password": user.password,
                        "phone_number": user.phone_number,
                        "address": address,
                    }
                )
                with open(DATA_FILE, "w", encoding="utf-8") as data_file:
                    json.dump(data, data_file, indent=4)

                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("auth.login"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("register.html")


    @auth.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            try:
                user = auth_service.login(
                    email=request.form.get("email"),
                    password=request.form.get("password"),
                )
                # Store the canonical customer id in session so other parts
                # of the app can detect the logged-in user.
                session["customer_id"] = user["customer_id"]
                session["email"] = user["email"]
                flash("Login successful.", "success")
                return redirect(url_for("homepage"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("login.html")

    
    @auth.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("homepage"))

    return auth


