import unittest
from datetime import date

import validators

TODAY = date(2026, 11, 24)


class ValidatorTests(unittest.TestCase):

    def test_valid_name(self):
        self.assertEqual(validators.validate_name("  Ana Cruz  "), "Ana Cruz")
        self.assertEqual(validators.validate_name("Jose Ma. Dela Peña"), "Jose Ma. Dela Peña")

    def test_invalid_names(self):
        for name in ["", "   ", "A", "Ana123", "Ana@Cruz", "x" * 61]:
            with self.assertRaises(ValueError):
                validators.validate_name(name)

    def test_phone_numbers(self):
        self.assertEqual(validators.validate_phone("09171234567"), "09171234567")
        self.assertEqual(validators.validate_phone("+63 917 123 4567"), "09171234567")
        self.assertEqual(validators.validate_phone("0917-123-4567"), "09171234567")
        for phone in ["", "12345", "08171234567", "091712345678", "0917abc4567"]:
            with self.assertRaises(ValueError):
                validators.validate_phone(phone)

    def test_email(self):
        self.assertEqual(validators.validate_email(""), "")
        self.assertEqual(validators.validate_email("Ana@Example.com"), "ana@example.com")
        for email in ["ana", "ana@", "@example.com", "ana@example", "an a@example.com"]:
            with self.assertRaises(ValueError):
                validators.validate_email(email)

    def test_date(self):
        self.assertEqual(validators.validate_date("2026-12-15", TODAY), "2026-12-15")
        # Boundary: today is allowed, yesterday is not.
        self.assertEqual(validators.validate_date("2026-11-24", TODAY), "2026-11-24")
        with self.assertRaises(ValueError):
            validators.validate_date("2026-11-23", TODAY)
        for text in ["2026-02-30", "15-12-2026", "tomorrow", ""]:
            with self.assertRaises(ValueError):
                validators.validate_date(text, TODAY)

    def test_time(self):
        # Boundary: 08:00 and 16:00 are the first and last start times.
        self.assertEqual(validators.validate_time("08:00"), "08:00")
        self.assertEqual(validators.validate_time("16:00"), "16:00")
        for text in ["07:00", "17:00", "09:30", "25:00", "nine", ""]:
            with self.assertRaises(ValueError):
                validators.validate_time(text)

    def test_amount(self):
        self.assertEqual(validators.validate_amount("1500"), 1500.0)
        self.assertEqual(validators.validate_amount("1,500.50"), 1500.5)
        self.assertEqual(validators.validate_amount("0.01"), 0.01)   # boundary
        for text in ["0", "-100", "abc", "12.345", ""]:
            with self.assertRaises(ValueError):
                validators.validate_amount(text)

    def test_menu_number(self):
        self.assertEqual(validators.validate_menu_number("3", 1, 8), 3)
        for text in ["0", "9", "two", ""]:
            with self.assertRaises(ValueError):
                validators.validate_menu_number(text, 1, 8)


if __name__ == "__main__":
    unittest.main()
