import unittest
from datetime import date, datetime

import appointment_system
import transaction_system

TODAY = date(2026, 11, 24)
NOW = datetime(2026, 11, 24, 10, 30, 0)
CASH = 1


class TransactionTests(unittest.TestCase):

    def setUp(self):
        self.appointments = []
        self.transactions = []
        # Legal Consultation, fee PHP 1,500.00
        self.appointment = appointment_system.create_appointment(
            self.appointments, "Ana Cruz", "09171234567", "", 1,
            "2026-12-01", "09:00", "Land title concern", TODAY)

    def pay(self, amount_text, method=CASH):
        return transaction_system.record_payment(
            self.appointment, self.transactions, amount_text, method, NOW)

    def test_fee_comes_from_service(self):
        self.assertEqual(transaction_system.get_balance(self.appointment, self.transactions), 1500.0)
        self.assertEqual(transaction_system.get_payment_status(self.appointment, self.transactions), "Unpaid")

    def test_partial_payment(self):
        transaction = self.pay("500")
        self.assertEqual(transaction["transaction_id"], "TXN-0001")
        self.assertEqual(transaction["amount_paid"], 500.0)
        self.assertEqual(transaction["balance_after"], 1000.0)
        self.assertEqual(transaction["service_fee"], 1500.0)
        self.assertEqual(transaction_system.get_payment_status(self.appointment, self.transactions),
                         "Partially Paid")

    def test_exact_full_payment(self):
        transaction = self.pay("1500")
        self.assertEqual(transaction["balance_after"], 0.0)
        self.assertEqual(transaction["change_given"], 0.0)
        self.assertEqual(transaction_system.get_payment_status(self.appointment, self.transactions), "Paid")

    def test_overpayment_gives_change(self):
        transaction = self.pay("2000")
        self.assertEqual(transaction["amount_paid"], 1500.0)
        self.assertEqual(transaction["change_given"], 500.0)
        self.assertEqual(transaction["balance_after"], 0.0)

    def test_two_payments_then_fully_paid(self):
        self.pay("1000")
        second = self.pay("500", method=2)
        self.assertEqual(second["transaction_id"], "TXN-0002")
        self.assertEqual(second["method"], "GCash")
        with self.assertRaises(ValueError):
            self.pay("1")                      # already fully paid
        self.assertEqual(len(self.transactions), 2)

    def test_invalid_payments_rejected(self):
        for amount in ["0", "-50", "abc", ""]:
            with self.assertRaises(ValueError):
                self.pay(amount)
        with self.assertRaises(ValueError):
            self.pay("500", method=9)
        self.assertEqual(self.transactions, [])

    def test_cancelled_appointment_cannot_be_paid(self):
        appointment_system.cancel_appointment(self.appointments, self.transactions, "APT-0001")
        with self.assertRaises(ValueError):
            self.pay("500")

    def test_payment_summary(self):
        second = appointment_system.create_appointment(
            self.appointments, "Ben Reyes", "09981112222", "", 2,
            "2026-12-01", "10:00", "Notarize affidavit", TODAY)    # fee PHP 300
        appointment_system.create_appointment(
            self.appointments, "Carla Dizon", "09185550000", "", 3,
            "2026-12-01", "11:00", "Affidavit of loss", TODAY)     # fee PHP 1,000
        self.pay("500")
        transaction_system.record_payment(second, self.transactions, "300", CASH, NOW)

        summary = transaction_system.get_payment_summary(self.appointments, self.transactions)
        self.assertEqual(summary["total_collected"], 800.0)
        self.assertEqual(summary["total_unpaid"], 2000.0)
        self.assertEqual(summary["paid_count"], 1)
        self.assertEqual(summary["partial_count"], 1)
        self.assertEqual(summary["unpaid_count"], 1)


if __name__ == "__main__":
    unittest.main()
