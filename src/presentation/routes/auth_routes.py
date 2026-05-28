from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from src.domain.models.customer import Customer
import json

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        phone_number = request.form.get('phone_number')
        password = request.form.get('password')
        if not all([name, address, phone_number, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('register.html')
        new_customer = Customer(name, address, phone_number, password)
        new_customer.create_user()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        if not all([name, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        with open('src/data/seeds/data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        if isinstance(data, dict):
            data = [data]
        result = next((item for item in data if item.get('name') == name), None)
        if result and result.get('password') == password:
            session['username'] = name
            flash('Login successful.', 'success')
            return redirect(url_for('homepage'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@auth.route('/logout')
def logout():

    return redirect(url_for('homepage'))
