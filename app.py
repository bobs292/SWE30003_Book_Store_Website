from flask import Flask, render_template, session, redirect, url_for, request, flash

from database import load_books

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session


def _coerce_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _get_cart():
    cart = session.get('cart')
    if not isinstance(cart, dict):
        return {}
    return {str(key): _coerce_int(value, 0) for key, value in cart.items()}


def _save_cart(cart):
    session['cart'] = cart


@app.context_processor
def inject_cart_count():
    cart = _get_cart()
    return {'cart_count': sum(cart.values())}


def _build_cart_items(books, cart):
    items = []
    subtotal = 0.0
    books_by_id = {str(book['id']): book for book in books}
    cart_changed = False

    for book_id in list(cart.keys()):
        if book_id not in books_by_id:
            cart.pop(book_id, None)
            cart_changed = True
            continue

        quantity = max(cart.get(book_id, 0), 0)
        if quantity == 0:
            cart.pop(book_id, None)
            cart_changed = True
            continue

        book = books_by_id[book_id]
        price = _coerce_float(book.get('price', 0.0), 0.0)
        line_total = price * quantity
        subtotal += line_total
        items.append({
            'book': book,
            'quantity': quantity,
            'line_total': line_total,
        })

    if cart_changed:
        _save_cart(cart)

    return items, subtotal

@app.route('/')
def homepage():
    return render_template('home.html')

@app.route('/catalogue')
def catalogue():
    books = load_books()
    return render_template('catalogue.html', books=books)

@app.route('/cart')
def cart():
    books = load_books()
    cart_data = _get_cart()
    cart_items, subtotal = _build_cart_items(books, cart_data)
    return render_template(
        'cart.html',
        cart_items=cart_items,
        subtotal=subtotal,
    )


@app.route('/cart/add', methods=['POST'])
def cart_add():
    books = load_books()
    books_by_id = {str(book['id']): book for book in books}
    book_id = request.form.get('book_id')
    quantity = _coerce_int(request.form.get('quantity'), 0)

    if not book_id or book_id not in books_by_id:
        return redirect(request.referrer or url_for('catalogue'))

    book = books_by_id[book_id]
    if book['stock'] <= 0:
        return redirect(request.referrer or url_for('catalogue'))

    if quantity <= 0:
        flash('Select a quantity before adding to cart.')
        return redirect(request.referrer or url_for('catalogue'))

    cart_data = _get_cart()
    current_qty = cart_data.get(book_id, 0)
    new_qty = min(current_qty + quantity, book['stock'])
    cart_data[book_id] = new_qty
    _save_cart(cart_data)
    flash(f"Added '{book['title']}' to your cart.")

    return redirect(request.referrer or url_for('catalogue'))


@app.route('/cart/update', methods=['POST'])
def cart_update():
    books = load_books()
    books_by_id = {str(book['id']): book for book in books}
    book_id = request.form.get('book_id')
    quantity = _coerce_int(request.form.get('quantity', 1), 1)

    cart_data = _get_cart()
    if not book_id or book_id not in cart_data:
        return redirect(url_for('cart'))

    if book_id not in books_by_id:
        cart_data.pop(book_id, None)
        _save_cart(cart_data)
        return redirect(url_for('cart'))

    stock = books_by_id[book_id]['stock']
    if quantity <= 0:
        cart_data.pop(book_id, None)
    else:
        cart_data[book_id] = min(quantity, stock)

    _save_cart(cart_data)
    return redirect(url_for('cart'))


@app.route('/cart/remove', methods=['POST'])
def cart_remove():
    book_id = request.form.get('book_id')
    cart_data = _get_cart()
    if book_id in cart_data:
        cart_data.pop(book_id, None)
        _save_cart(cart_data)
    return redirect(url_for('cart'))


@app.route('/cart/clear', methods=['POST'])
def cart_clear():
    _save_cart({})
    return redirect(url_for('cart'))

@app.route('/logout')
def logout(): 
    # TODO: Impleement Logout logic
    return redirect(url_for('homepage'))


@app.route('/checkout')
def checkout():
    books = load_books()
    cart_data = _get_cart()
    cart_items, subtotal = _build_cart_items(books, cart_data)
    return render_template(
        'checkout.html',
        cart_items=cart_items,
        subtotal=subtotal,
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)