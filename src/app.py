from flask import Flask, render_template
from src.presentation.routes.auth_routes import auth
from src.presentation.routes.catalogue_routes import catalogue
from src.presentation.routes.order_routes import order

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

app.register_blueprint(auth)
app.register_blueprint(catalogue)
app.register_blueprint(order)

@app.route('/')
def homepage():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
