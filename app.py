from flask import Flask, render_template, session, redirect, url_for, request, flash

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
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)