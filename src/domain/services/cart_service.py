class CartService:
    """Manages cart operations and calculations."""

    @staticmethod
    def safe_int(value, default=0):
        """Safely convert value to int."""
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def safe_float(value, default=0.0):
        """Safely convert value to float."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def normalize_cart(cart):
        """
        Normalizes cart dictionary, coercing values to integers.

        Returns normalized cart dict.
        """
        if not isinstance(cart, dict):
            return {}
        return {str(key): CartService.safe_int(value, 0) for key, value in cart.items()}

    @staticmethod
    def build_cart_items(books, cart):
        """
        Builds list of cart items with subtotal calculation.

        Removes items no longer in catalogue or with zero quantity.
        Returns (items, subtotal, cart_changed).
        """
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
            price = CartService.safe_float(book.get("price", 0.0), 0.0)
            line_total = price * quantity
            subtotal += line_total
            items.append(
                {
                    "book": book,
                    "quantity": quantity,
                    "line_total": line_total,
                }
            )

        return items, subtotal, cart_changed
