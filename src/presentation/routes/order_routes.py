from flask import Blueprint, flash, redirect, render_template, request, session, url_for

#TODO Reimplement logic verification logic LINE 201 + 232

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
    cart = session.get("cart")
    if not isinstance(cart, dict):
        return {}
    return {str(key): _coerce_int(value, 0) for key, value in cart.items()}


def _save_cart(cart):
    session["cart"] = cart


def _build_cart_items(books, cart):
    items = []
    subtotal = 0.0
    books_by_id = {str(book["id"]): book for book in books}
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
        price = _coerce_float(book.get("price", 0.0), 0.0)
        line_total = price * quantity
        subtotal += line_total
        items.append(
            {
                "book": book,
                "quantity": quantity,
                "line_total": line_total,
            }
        )

    if cart_changed:
        _save_cart(cart)

    return items, subtotal


def create_order_routes(catalogue_service, checkout_service, customer_repo):
    order = Blueprint("order", __name__)

    @order.route("/cart")
    def cart():
        books = catalogue_service.list_books()
        cart_data = _get_cart()
        cart_items, subtotal = _build_cart_items(books, cart_data)
        total_items = sum(cart_data.values()) if cart_data else 0
        return render_template(
            "cart.html",
            cart_items=cart_items,
            subtotal=subtotal,
            total_items=total_items,
        )

    @order.route("/cart/add", methods=["POST"])
    def cart_add():
        books = catalogue_service.list_books()
        books_by_id = {str(book["id"]): book for book in books}
        book_id = request.form.get("book_id")
        quantity = _coerce_int(request.form.get("quantity"), 0)

        if not book_id or book_id not in books_by_id:
            return redirect(request.referrer or url_for("catalogue.catalogue_page"))

        book = books_by_id[book_id]
        if book["stock"] <= 0:
            return redirect(request.referrer or url_for("catalogue.catalogue_page"))

        if quantity <= 0:
            flash("Select a quantity before adding to cart.", "warning")
            return redirect(request.referrer or url_for("catalogue.catalogue_page"))

        cart_data = _get_cart()
        current_qty = cart_data.get(book_id, 0)
        new_qty = min(current_qty + quantity, book["stock"])
        cart_data[book_id] = new_qty
        _save_cart(cart_data)
        flash(f"Added '{book['title']}' to your cart.", "success")

        return redirect(request.referrer or url_for("catalogue.catalogue_page"))

    @order.route("/cart/update", methods=["POST"])
    def cart_update():
        books = catalogue_service.list_books()
        books_by_id = {str(book["id"]): book for book in books}
        book_id = request.form.get("book_id")
        quantity = _coerce_int(request.form.get("quantity", 1), 1)

        cart_data = _get_cart()
        if not book_id or book_id not in cart_data:
            return redirect(url_for("order.cart"))

        current_qty = cart_data.get(book_id, 0)

        if book_id not in books_by_id:
            cart_data.pop(book_id, None)
            _save_cart(cart_data)
            return redirect(url_for("order.cart"))

        stock = books_by_id[book_id]["stock"]
        book_title = books_by_id[book_id].get("title", "Item")
        if quantity <= 0:
            cart_data.pop(book_id, None)
            flash(f"Removed '{book_title}' from your cart.", "success")
        else:
            updated_qty = min(quantity, stock)
            if updated_qty == current_qty:
                flash(f"'{book_title}' quantity is already {current_qty}.", "warning")
            else:
                cart_data[book_id] = updated_qty
                flash(f"Updated '{book_title}' quantity to {updated_qty}.", "success")

        _save_cart(cart_data)
        return redirect(url_for("order.cart"))

    @order.route("/cart/remove", methods=["POST"])
    def cart_remove():
        books = catalogue_service.list_books()
        books_by_id = {str(book["id"]): book for book in books}
        book_id = request.form.get("book_id")
        cart_data = _get_cart()
        if book_id in cart_data:
            cart_data.pop(book_id, None)
            _save_cart(cart_data)
            if book_id in books_by_id:
                flash(
                    f"Removed '{books_by_id[book_id]['title']}' from your cart.",
                    "success",
                )
        return redirect(url_for("order.cart"))

    @order.route("/cart/clear", methods=["POST"])
    def cart_clear():
        cart_data = _get_cart()
        total_items = sum(cart_data.values()) if cart_data else 0
        _save_cart({})
        if total_items:
            flash(f"Cleared {total_items} item(s) from your cart.", "success")
        return redirect(url_for("order.cart"))

    @order.route("/confirmation/<int:order_id>")
    def confirmation(order_id):
        return render_template("order_confirmation.html", order_id=order_id)
            
    @order.route("/checkout", methods=["GET", "POST"])
    def checkout():
        if request.method == "POST":
        # get the form data
            address    = request.form.get("address")
            city       = request.form.get("city")
            postcode   = request.form.get("postcode")
            phone      = request.form.get("phone")
            shipping_address = f"{address}, {city}, {postcode}"
        #get cart data
            cart_data = _get_cart()
            if not cart_data:
                flash("Your cart is empty.", "error")
                return redirect(url_for("order.cart"))
        #Retrieve full book details (needed for the service)
            books = catalogue_service.list_books()
            cart_items, subtotal = _build_cart_items(books, cart_data)
            if not cart_items:
                flash("No valid items in cart.", "error")
                return redirect(url_for("order.cart"))
        #prepare input for serive
            service_items = []
            for item in cart_items:
                service_items.append({
                    "book_id": item["book"]["id"],
                    "quantity": item["quantity"],
                    "unit_price": item["book"]["price"]
                })
            customer_id = 1 

        # # Check if the customer is logged in
        #     customer_id = session.get("user_id")  
        #     if not customer_id:
        #         flash("Please log in to checkout.", "error")
        #         return redirect(url_for("auth.login"))
        #call the service
            try:
                order, invoice = checkout_service.process_checkout(
                    customer_id=customer_id,
                    cart_items=service_items,
                    shipping_address=shipping_address,
                    shipping_phone=phone,
                    payment_details={}
                )
                _save_cart({})
                flash(f"Order #{order.order_id} placed! Invoice #{invoice.invoice_id}", "success")
                #to display books in confirm screne
                books = catalogue_service.list_books()
                books_by_id = {str(book["id"]): book for book in books}
                for item in order.items:
                    book = books_by_id.get(str(item.book_id))
                    item.book_title = book["title"] if book else f"Book {item.book_id}"

                return render_template("order_confirmation.html", order=order, invoice=invoice)

            except ValueError as e:
                flash(str(e), "error")
                return redirect(url_for("order.cart"))
            except Exception as e:
                flash(f"Checkout failed: {str(e)}", "error")
                return redirect(url_for("order.cart"))
        # GET METHOD 
        books = catalogue_service.list_books()
        cart_data = _get_cart()
        cart_items, subtotal = _build_cart_items(books, cart_data)
        
        customer = None
        # customer_id = session.get("user_id")
        # if customer_id:
        #     customer = customer_repo.find_by_id(customer_id)

        return render_template(
            "checkout.html",
            cart_items=cart_items,
            subtotal=subtotal,
            customer=customer
        ) 
    return order

