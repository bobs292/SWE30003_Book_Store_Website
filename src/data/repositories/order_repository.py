import sqlite3
from datetime import datetime
from src.data.database import get_connection
from src.domain.models.order import Order, OrderItem
from src.domain.repositories.order_repository import OrderRepository

class SqliteOrderRepository(OrderRepository):
    def save(self, order: Order) -> Order:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO orders (customer_id, order_date, total_amount, shipping_address, shipping_phone)
            VALUES (?, ?, ?, ?, ?)
        """, (
            order.customer_id,
            order.order_date.isoformat(),
            order.total_amount,
            order.shipping_address,
            order.shipping_phone,
        ))
        order_id = cursor.lastrowid
        order.order_id = order_id

        # insert each order item
        for item in order.items:
            cursor.execute("""
                INSERT INTO order_items (order_id, book_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            """, (order_id, item.book_id, item.quantity, item.unit_price))

        conn.commit()
        conn.close()
        return order

    def find_by_id(self, order_id: int) -> Order | None:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
        item_rows = cursor.fetchall()
        items = [
            OrderItem(
                book_id=ir["book_id"],
                quantity=ir["quantity"],
                unit_price=ir["unit_price"],
            )
            for ir in item_rows
        ]
        conn.close()

        return Order(
            order_id=row["order_id"],
            customer_id=row["customer_id"],
            order_date=datetime.fromisoformat(row["order_date"]),
            total_amount=row["total_amount"],
            shipping_address=row["shipping_address"],
            shipping_phone=row["shipping_phone"],
            items=items,
        )