from src.data.database import get_connection
from src.domain.models.invoice import Invoice
from src.domain.repositories.invoice_repository import InvoiceRepository

class SqliteInvoiceRepository(InvoiceRepository):
    def save(self, invoice: Invoice) -> Invoice:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO invoices (order_id, invoice_date, amount_due)
            VALUES (?, ?, ?)
        """, (
            invoice.order_id,
            invoice.invoice_date.isoformat(),
            invoice.amount_due,
        ))
        invoice.invoice_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return invoice