import unittest
from datetime import date

import appointment_system
import services

TODAY = date(2026, 11, 24)
DAY = "2026-12-01"


def book(appointments, name, time_text, service_number=1, day=DAY):
    """Book an appointment with sample (made-up) client details."""
    return appointment_system.create_appointment(
        appointments, name, "09171234567", "", service_number,
        day, time_text, "Needs advice on a land title.", TODAY)


class ServiceTests(unittest.TestCase):

    def test_services_are_tuples(self):
        self.assertEqual(type(services.LEGAL_SERVICES), tuple)
        self.assertEqual(type(services.LEGAL_SERVICES[0]), tuple)

    def test_service_lookup(self):
        self.assertEqual(services.get_service_by_number(1)[1], "Legal Consultation")
        self.assertEqual(services.get_service_by_code("S2")[2], 300.0)
        self.assertIsNone(services.get_service_by_code("S99"))
        with self.assertRaises(ValueError):
            services.get_service_by_number(0)
        with self.assertRaises(ValueError):
            services.get_service_by_number(len(services.LEGAL_SERVICES) + 1)

    def test_fee_table_is_dictionary(self):
        fees = services.build_fee_table()
        self.assertEqual(type(fees), dict)
        self.assertEqual(fees["S1"], 1500.0)
        self.assertEqual(len(fees), len(services.LEGAL_SERVICES))

    def test_format_money(self):
        self.assertEqual(services.format_money(1500), "PHP 1,500.00")
        self.assertEqual(services.format_money(0.5), "PHP 0.50")


class AppointmentTests(unittest.TestCase):

    def setUp(self):
        self.appointments = []
        self.transactions = []

    def test_book_appointment_fills_in_fee(self):
        appointment = book(self.appointments, "Ana Cruz", "09:00", service_number=6)
        self.assertEqual(appointment["appointment_id"], "APT-0001")
        self.assertEqual(appointment["service_name"], "Contract Drafting")
        self.assertEqual(appointment["service_fee"], 5000.0)
        self.assertEqual(appointment["status"], "Booked")
        self.assertEqual(len(self.appointments), 1)

    def test_ids_go_up(self):
        book(self.appointments, "Ana Cruz", "09:00")
        second = book(self.appointments, "Ben Reyes", "10:00")
        self.assertEqual(second["appointment_id"], "APT-0002")

    def test_same_slot_rejected(self):
        book(self.appointments, "Ana Cruz", "09:00")
        with self.assertRaises(ValueError):
            book(self.appointments, "Ben Reyes", "09:00")
        self.assertEqual(len(self.appointments), 1)

    def test_same_time_other_day_allowed(self):
        book(self.appointments, "Ana Cruz", "09:00")
        book(self.appointments, "Ben Reyes", "09:00", day="2026-12-02")
        self.assertEqual(len(self.appointments), 2)

    def test_invalid_details_rejected(self):
        with self.assertRaises(ValueError):
            appointment_system.create_appointment(
                self.appointments, "Ana Cruz", "12345", "", 1, DAY, "09:00", "Advice", TODAY)
        with self.assertRaises(ValueError):
            appointment_system.create_appointment(
                self.appointments, "Ana Cruz", "09171234567", "", 99, DAY, "09:00", "Advice", TODAY)
        with self.assertRaises(ValueError):
            appointment_system.create_appointment(
                self.appointments, "Ana Cruz", "09171234567", "", 1, DAY, "09:00", "  ", TODAY)
        self.assertEqual(self.appointments, [])

    def test_available_times(self):
        self.assertEqual(len(appointment_system.get_available_times(self.appointments, DAY)), 9)
        book(self.appointments, "Ana Cruz", "08:00")
        book(self.appointments, "Ben Reyes", "16:00")
        free = appointment_system.get_available_times(self.appointments, DAY)
        self.assertEqual(len(free), 7)
        self.assertNotIn("08:00", free)
        self.assertNotIn("16:00", free)

    def test_find_and_search(self):
        book(self.appointments, "Ana Cruz", "09:00")
        book(self.appointments, "Ben Reyes", "10:00")
        self.assertIsNotNone(appointment_system.find_appointment(self.appointments, "apt-0002"))
        self.assertIsNone(appointment_system.find_appointment(self.appointments, "APT-0099"))
        self.assertEqual(len(appointment_system.search_by_client(self.appointments, "cruz")), 1)
        self.assertEqual(len(appointment_system.search_by_client(self.appointments, "zzz")), 0)

    def test_cancel_frees_the_slot(self):
        book(self.appointments, "Ana Cruz", "09:00")
        appointment_system.cancel_appointment(self.appointments, self.transactions, "APT-0001")
        self.assertEqual(self.appointments[0]["status"], "Cancelled")
        book(self.appointments, "Ben Reyes", "09:00")   # slot is free again
        with self.assertRaises(ValueError):
            appointment_system.cancel_appointment(self.appointments, self.transactions, "APT-0001")

    def test_cannot_cancel_paid_appointment(self):
        book(self.appointments, "Ana Cruz", "09:00")
        self.transactions.append({"appointment_id": "APT-0001", "amount_paid": 500.0})
        with self.assertRaises(ValueError):
            appointment_system.cancel_appointment(self.appointments, self.transactions, "APT-0001")
        self.assertEqual(self.appointments[0]["status"], "Booked")


if __name__ == "__main__":
    unittest.main()
