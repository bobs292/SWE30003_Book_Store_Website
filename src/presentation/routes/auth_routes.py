from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from email_validator import validate_email, EmailNotValidError

from smartystreets_python_sdk import BasicAuthCredentials, ClientBuilder
from smartystreets_python_sdk.international_street import Lookup as InternationalLookup

import phonenumbers
import string
#DATE_FILE = Add JSON
#AUTH_ID = FOR ADDRESS
#AUTH_TOKEN = FOR ADDRESS
def create_auth_routes(auth_service):
    
    def check_email(email):
        try:
            validate_email(email, check_deliverability=True)
            return None
        except EmailNotValidError as e:
            return str(e)  
 
    def check_password(password):
        if len(password) >= 12 and any(char in string.punctuation for char in password):
            return None
        return "Password must be 12 or more characters and include at least 1 special character"
 
    def check_phone_number(number_string, country_code=None):

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
        credentials = BasicAuthCredentials(auth_id, auth_token)
        client = ClientBuilder(credentials).build_international_street_api_client()
        lookup = InternationalLookup()
        lookup.country = "Australia"
        lookup.address1 = address
        try:
            result = client.send(lookup)
            if result.result:
                return None
            return "Address could not be verified"
        except Exception as e:
            return str(e)
 
    def test_user(first_name, last_name, address, email, password, phone_number):
        # FIX: was comparing the string itself to an int, not its length
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
 
        with open(DATA_FILE, "r") as file:
            data = json.load(file)
        if email in data:
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
                new_user = auth_service.register(
                    first_name=request.form.get("first_name"),
                    last_name=request.form.get("last_name"),
                    email=request.form.get("email"),
                    address=request.form.get("address"),
                    password=request.form.get("password"),
                    phone_number=request.form.get("phone_number") or None
                )
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
                session["customer_id"] = user["customer_id"]
                flash("Login successful.", "success")
                return redirect(url_for("homepage"))
            except ValueError as e:
                flash(str(e), "error")
        return render_template("login.html")

    
    @auth.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("homepage"))


