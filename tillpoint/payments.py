
"""Payment provider webhooks. The provider retries a delivery until it gets a 2xx, so events can repeat."""
from . import db


class PaymentError(Exception):
    pass


class Payments:
    def __init__(self, conn):
        self.conn = conn

    def handle_event(self, event, now=None):
        """Handle successful payment events safely."""
        if event.get("type") != "payment.succeeded":
            return None

        self.conn.execute("BEGIN IMMEDIATE")

        try:
            order = self.conn.execute(
                "SELECT * FROM orders WHERE id = ?",
                (event["order_id"],)
            ).fetchone()

            if order is None:
                raise PaymentError(
                    f"payment for unknown order {event['order_id']}"
                )

            if order["status"] == "cancelled":
                raise PaymentError(f"order {order['id']} is cancelled")

            # Ignore the same webhook event if it was already received.
            existing = self.conn.execute(
                "SELECT 1 FROM payments WHERE event_id = ?",
                (event["id"],)
            ).fetchone()

            if existing is not None:
                self.conn.execute("COMMIT")
                return order["status"]

            amount = event["amount_cents"]

            if amount <= 0:
                raise PaymentError("payment amount must be positive")

            already_paid = self.paid_cents(order["id"])

            # Reject payments that would exceed the order total.
            if already_paid + amount > order["total_cents"]:
                raise PaymentError(
                    f"payment exceeds order total for order {order['id']}"
                )

            self.conn.execute(
                """
                INSERT INTO payments
                (order_id, event_id, amount_cents, received_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    order["id"],
                    event["id"],
                    amount,
                    db.to_iso(now or db.utcnow()),
                ),
            )

            new_paid_total = already_paid + amount

            if (
                order["status"] == "pending"
                and new_paid_total == order["total_cents"]
            ):
                self.conn.execute(
                    "UPDATE orders SET status = 'paid' WHERE id = ?",
                    (order["id"],),
                )
                self.conn.execute("COMMIT")
                return "paid"

            self.conn.execute("COMMIT")
            return order["status"]

        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def paid_cents(self, order_id):
        row = self.conn.execute(
            """
            SELECT COALESCE(SUM(amount_cents), 0) AS paid
            FROM payments
            WHERE order_id = ?
            """,
            (order_id,)
        ).fetchone()
        return row["paid"]
