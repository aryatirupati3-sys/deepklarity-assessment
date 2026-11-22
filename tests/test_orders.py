
import unittest
import os
import tempfile
import threading
from datetime import datetime, timezone

from tillpoint import db, reports
from tillpoint.api import App
from tillpoint.catalog import OutOfStock
from tillpoint.payments import PaymentError


class OrderDeskTest(unittest.TestCase):

    def setUp(self):
        self.conn = db.connect()
        self.app = App(self.conn)
        self.app.catalog.add_product("MUG", "Mug", 1200, stock=10)
        self.app.catalog.add_product("TEE", "T-shirt", 2500, stock=3)
        self.conn.execute(
            "INSERT INTO coupons (code, kind, value) VALUES ('TEN', 'percent', 10)"
        )

    def tearDown(self):
        self.conn.close()

    def test_order_totals_with_tax(self):
        order = self.app.orders.create(
            "ana", [("MUG", 2), ("TEE", 1)], region="CA"
        )
        self.assertEqual(order["subtotal_cents"], 4900)
        self.assertEqual(order["tax_cents"], 355)
        self.assertEqual(order["total_cents"], 5255)
        self.assertEqual(self.app.catalog.get_product("MUG").stock, 8)

    def test_coupon_takes_ten_percent(self):
        order = self.app.orders.create(
            "ana", [("MUG", 1)], coupon_code="TEN"
        )
        self.assertEqual(order["discount_cents"], 120)
        self.assertEqual(order["total_cents"], 1080)

    def test_coupon_tax_calculated_after_discount(self):
        order = self.app.orders.create(
            "ana",
            [("MUG", 1)],
            region="CA",
            coupon_code="TEN"
        )
        self.assertEqual(order["discount_cents"], 120)
        self.assertEqual(order["tax_cents"], 78)
        self.assertEqual(order["total_cents"], 1158)

    def test_out_of_stock(self):
        with self.assertRaises(OutOfStock):
            self.app.orders.create("ana", [("TEE", 4)])
        self.assertEqual(self.app.catalog.get_product("TEE").stock, 3)

    def test_payment_marks_order_paid(self):
        order = self.app.orders.create("ana", [("MUG", 1)])
        status, payload = self.app.handle(
            "POST",
            "/webhooks/payments",
            {
                "id": "evt_1",
                "type": "payment.succeeded",
                "order_id": order["id"],
                "amount_cents": 1200
            }
        )
        self.assertEqual((status, payload["status"]), (200, "paid"))

    def test_duplicate_payment_event(self):
        order = self.app.orders.create("ana", [("MUG", 1)])
        event = {
            "id": "evt_duplicate",
            "type": "payment.succeeded",
            "order_id": order["id"],
            "amount_cents": 1200
        }
        self.app.payments.handle_event(event)
        self.app.payments.handle_event(event)
        self.assertEqual(self.app.payments.paid_cents(order["id"]), 1200)

    def test_cancel_paid_order_restocks(self):
        order = self.app.orders.create("ana", [("TEE", 2)])
        self.app.payments.handle_event(
            {
                "id": "evt_2",
                "type": "payment.succeeded",
                "order_id": order["id"],
                "amount_cents": 5000
            }
        )
        self.app.orders.cancel(order["id"])
        self.assertEqual(self.app.catalog.get_product("TEE").stock, 3)

    def test_cancel_pending_order_restocks(self):
        order = self.app.orders.create("ana", [("MUG", 1)])
        self.app.orders.cancel(order["id"])
        self.assertEqual(self.app.catalog.get_product("MUG").stock, 10)

    def test_daily_sales(self):
        order = self.app.orders.create("ana", [("MUG", 1)])
        noon = datetime(2025, 3, 10, 12, 0, tzinfo=timezone.utc)
        self.app.payments.handle_event(
            {
                "id": "evt_3",
                "type": "payment.succeeded",
                "order_id": order["id"],
                "amount_cents": 1200
            },
            now=noon
        )
        self.assertEqual(
            reports.daily_sales(self.conn, "2025-03-10"),
            {
                "day": "2025-03-10",
                "revenue_cents": 1200,
                "orders": 1
            }
        )

    def test_daily_sales_india_timezone(self):
        order = self.app.orders.create("ana", [("MUG", 1)])
        payment_time = datetime(
            2025, 3, 10, 20, 0, tzinfo=timezone.utc
        )
        self.app.payments.handle_event(
            {
                "id": "evt_india",
                "type": "payment.succeeded",
                "order_id": order["id"],
                "amount_cents": 1200
            },
            now=payment_time
        )
        self.assertEqual(
            reports.daily_sales(
                self.conn,
                "2025-03-11",
                utc_offset_minutes=330
            ),
            {
                "day": "2025-03-11",
                "revenue_cents": 1200,
                "orders": 1
            }
        )

    def test_price_change(self):
        self.app.handle(
            "PUT",
            "/products/MUG",
            {"price_cents": 1500}
        )
        self.assertEqual(
            self.app.catalog.get_product("MUG").price_cents,
            1500
        )

    def test_concurrent_orders_do_not_oversell(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)

        try:
            setup_conn = db.connect(path)
            setup_app = App(setup_conn)
            setup_app.catalog.add_product(
                "LIMITED", "Limited Product", 1000, stock=1
            )
            setup_conn.close()

            results = []
            results_lock = threading.Lock()

            def create_order(customer):
                conn = db.connect(path)
                try:
                    app = App(conn)
                    app.orders.create(customer, [("LIMITED", 1)])
                    result = "success"
                except Exception as exc:
                    result = type(exc).__name__
                finally:
                    conn.close()

                with results_lock:
                    results.append(result)

            t1 = threading.Thread(target=create_order, args=("ana",))
            t2 = threading.Thread(target=create_order, args=("bob",))

            t1.start()
            t2.start()
            t1.join()
            t2.join()

            check_conn = db.connect(path)
            try:
                remaining = check_conn.execute(
                    "SELECT stock FROM products WHERE sku = 'LIMITED'"
                ).fetchone()["stock"]
            finally:
                check_conn.close()

            print("Concurrent order results:", results)
            self.assertEqual(results.count("success"), 1)
            self.assertEqual(remaining, 0)

        finally:
            for suffix in ("", "-journal", "-wal", "-shm"):
                file_path = path + suffix
                if os.path.exists(file_path):
                    os.remove(file_path)

    def test_reject_payment_amount_greater_than_order_total(self):
        order = self.app.orders.create("ana", [("MUG", 1)])

        with self.assertRaises(PaymentError):
            self.app.payments.handle_event({
                "id": "evt_overpayment",
                "type": "payment.succeeded",
                "order_id": order["id"],
                "amount_cents": 1500
            })

        self.assertEqual(
            self.app.payments.paid_cents(order["id"]),
            0
        )


if __name__ == "__main__":
    unittest.main()
