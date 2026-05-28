from flask import Flask, render_template, session, redirect, url_for, request, flash
from domain.models.customer import Customer
import json
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/catalogue')
def catalogue():
    return render_template('catalogue.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

@app.route('/logout')
def logout(): 
    # TODO: Impleement Logout logic
    return redirect(url_for('homepage'))

@app.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form.get('username')
        password = request.form.get('password')
        if not all([name, password]):
            flash('Please fill in all fields.', 'error')
            return render_template('login.html')
        with open('data/data.json', 'r', encoding='utf-8') as file:
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

if __name__ == '__main__':
    app.run(debug=True)