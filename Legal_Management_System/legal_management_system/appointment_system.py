"""
appointment_system.py - Booking, finding, searching and cancelling appointments.

All appointments are kept in a LIST. Each appointment is a DICTIONARY, so
every detail can be read by its name, for example appointment["client_name"].

Rules:
- One lawyer, so only one appointment per date and time slot.
- Each appointment lasts one hour; it starts on the hour from 08:00 to 16:00.
- The service fee is copied automatically from the chosen legal service.
- An appointment that already has a payment cannot be cancelled.
"""

import services
import validators

APPOINTMENT_STATUSES = ("Booked", "Cancelled")


def generate_appointment_id(appointments):
    """Return the next ID, e.g. 'APT-0001', 'APT-0002', ..."""
    highest = 0
    for appointment in appointments:
        number = int(appointment["appointment_id"].split("-")[1])
        if number > highest:
            highest = number
    return "APT-" + str(highest + 1).zfill(4)


def is_slot_taken(appointments, date_text, time_text):
    """True if a booked (not cancelled) appointment already uses this slot."""
    for appointment in appointments:
        if (appointment["date"] == date_text and appointment["time"] == time_text
                and appointment["status"] == "Booked"):
            return True
    return False


def get_available_times(appointments, date_text):
    """Return a list of the free start times on a date, e.g. ['08:00', '10:00']."""
    free_times = []
    hour = validators.OPENING_HOUR
    while hour <= validators.LAST_START_HOUR:
        time_text = str(hour).zfill(2) + ":00"
        if not is_slot_taken(appointments, date_text, time_text):
            free_times.append(time_text)
        hour = hour + 1
    return free_times


def create_appointment(appointments, client_name, contact_number, email,
                       service_number, date_text, time_text, concern, today=None):
    """
    Check the client's information, book the appointment and add it to the
    list. Returns the new appointment dictionary.
    Raises ValueError if any information is invalid or the slot is taken.
    """
    client_name = validators.validate_name(client_name)
    contact_number = validators.validate_phone(contact_number)
    email = validators.validate_email(email)
    service = services.get_service_by_number(service_number)
    date_text = validators.validate_date(date_text, today)
    time_text = validators.validate_time(time_text)
    concern = validators.validate_concern(concern)

    if is_slot_taken(appointments, date_text, time_text):
        raise ValueError("Sorry, " + date_text + " at " + time_text
                         + " is already booked. Please choose another time.")

    code, service_name, fee = service
    appointment = {
        "appointment_id": generate_appointment_id(appointments),
        "client_name": client_name,
        "contact_number": contact_number,
        "email": email,
        "service_code": code,
        "service_name": service_name,
        "service_fee": fee,
        "date": date_text,
        "time": time_text,
        "concern": concern,
        "status": "Booked",
    }
    appointments.append(appointment)
    return appointment


def find_appointment(appointments, appointment_id):
    """Return the appointment with this ID (not case-sensitive), or None."""
    appointment_id = appointment_id.strip().upper()
    for appointment in appointments:
        if appointment["appointment_id"] == appointment_id:
            return appointment
    return None


def search_by_client(appointments, search_text):
    """Return a list of appointments whose client name contains the text."""
    search_text = search_text.strip().lower()
    results = []
    for appointment in appointments:
        if search_text in appointment["client_name"].lower():
            results.append(appointment)
    return results


def cancel_appointment(appointments, transactions, appointment_id):
    """
    Cancel a booked appointment and free its time slot.
    Returns the cancelled appointment. Raises ValueError if not allowed.
    """
    appointment = find_appointment(appointments, appointment_id)
    if appointment is None:
        raise ValueError("No appointment found with ID " + appointment_id.strip().upper() + ".")
    if appointment["status"] == "Cancelled":
        raise ValueError("This appointment is already cancelled.")
    for transaction in transactions:
        if transaction["appointment_id"] == appointment["appointment_id"]:
            raise ValueError("This appointment already has a payment and cannot be "
                             "cancelled. Please see the office about a refund.")
    appointment["status"] = "Cancelled"
    return appointment
