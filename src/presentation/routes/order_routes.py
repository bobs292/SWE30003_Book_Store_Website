from flask import Blueprint, render_template

order = Blueprint('order', __name__)

@order.route('/cart')
def cart():
    return render_template('cart.html')
