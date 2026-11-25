import os
import shutil
import tempfile
import unittest
from datetime import date, datetime

import appointment_system
import file_handler
import transaction_system

TODAY = date(2026, 11, 24)
NOW = datetime(2026, 11, 24, 10, 30, 0)


class FileHandlerTests(unittest.TestCase):
    """Every test uses its own temporary folder, so real records are never touched."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.appointments_file = os.path.join(self.folder, "appointments.json")
        self.transactions_file = os.path.join(self.folder, "transactions.csv")
        self.appointments = []
        self.transactions = []
        self.appointment = appointment_system.create_appointment(
            self.appointments, "Ana Cruz", "09171234567", "ana@example.com", 1,
            "2026-12-01", "09:00", "Land title concern", TODAY)

    def tearDown(self):
        shutil.rmtree(self.folder, ignore_errors=True)

    def test_missing_files_start_empty(self):
        appointments, warning = file_handler.load_appointments(self.appointments_file)
        self.assertEqual(appointments, [])
        self.assertEqual(warning, "")
        transactions, warning = file_handler.load_transactions(self.transactions_file)
        self.assertEqual(transactions, [])

    def test_appointments_saved_and_loaded(self):
        file_handler.save_appointments(self.appointments, self.appointments_file)
        loaded, warning = file_handler.load_appointments(self.appointments_file)
        self.assertEqual(loaded, self.appointments)
        self.assertEqual(warning, "")

    def test_damaged_appointments_file(self):
        with open(self.appointments_file, "w", encoding="utf-8") as damaged:
            damaged.write("{ this is not valid JSON")
        loaded, warning = file_handler.load_appointments(self.appointments_file)
        self.assertEqual(loaded, [])
        self.assertIn("damaged", warning)
        self.assertTrue(os.path.exists(self.appointments_file + ".damaged"))

    def test_incomplete_appointment_record_skipped(self):
        records = [self.appointment, {"appointment_id": "APT-0002"}]
        file_handler.save_appointments(records, self.appointments_file)
        loaded, warning = file_handler.load_appointments(self.appointments_file)
        self.assertEqual(len(loaded), 1)
        self.assertIn("1 damaged", warning)

    def test_payments_appended_and_loaded(self):
        first = transaction_system.record_payment(self.appointment, self.transactions, "500", 1, NOW)
        second = transaction_system.record_payment(self.appointment, self.transactions, "1000", 2, NOW)
        file_handler.append_transaction(first, self.transactions_file)
        file_handler.append_transaction(second, self.transactions_file)

        loaded, warning = file_handler.load_transactions(self.transactions_file)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["amount_paid"], 500.0)       # converted back to a number
        self.assertEqual(loaded[1]["method"], "GCash")
        self.assertEqual(warning, "")
        # The header row is written only once.
        with open(self.transactions_file, "r", encoding="utf-8") as csv_file:
            text = csv_file.read()
        self.assertEqual(text.count("transaction_id"), 1)

    def test_damaged_payment_row_skipped(self):
        first = transaction_system.record_payment(self.appointment, self.transactions, "500", 1, NOW)
        file_handler.append_transaction(first, self.transactions_file)
        with open(self.transactions_file, "a", encoding="utf-8") as broken:
            broken.write("TXN-0002,APT-0001,Ana Cruz,Legal Consultation,1500,abc,0,Cash,1000,2026-11-24\n")
            broken.write("TXN-0003,too,few,columns\n")
        loaded, warning = file_handler.load_transactions(self.transactions_file)
        self.assertEqual(len(loaded), 1)
        self.assertIn("2 damaged", warning)

    def test_receipt_file(self):
        transaction = transaction_system.record_payment(self.appointment, self.transactions, "2000", 1, NOW)
        path = file_handler.save_receipt(transaction, self.appointment, self.folder)
        self.assertTrue(path.endswith("TXN-0001.txt"))
        with open(path, "r", encoding="utf-8") as receipt:
            text = receipt.read()
        self.assertIn("Ana Cruz", text)
        self.assertIn("PHP 1,500.00", text)
        self.assertIn("Change        : PHP 500.00", text)

    def test_error_log_appends(self):
        log_file = os.path.join(self.folder, "error_log.txt")
        file_handler.log_error(ValueError("first problem"), log_file)
        file_handler.log_error(KeyError("second problem"), log_file)
        with open(log_file, "r", encoding="utf-8") as log:
            lines = log.readlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("ValueError: first problem", lines[0])


if __name__ == "__main__":
    unittest.main()
