"""
validators.py - Checks the information typed by the user.

Every function either returns a cleaned value or raises ValueError with a
message that can be shown to the user.
"""

from datetime import date, datetime

OPENING_HOUR = 8         # first appointment starts at 08:00
LAST_START_HOUR = 16     # last appointment starts at 16:00 (ends 17:00)
NAME_SYMBOLS = " .-'"    # allowed in names besides letters


def validate_required(text, field_name):
    """Return the trimmed text, or raise ValueError if it is empty."""
    text = text.strip()
    if text == "":
        raise ValueError(field_name + " is required.")
    return text


def validate_name(name):
    """A client name: 2 to 60 characters, letters and . - ' only."""
    name = validate_required(name, "Name")
    if len(name) < 2 or len(name) > 60:
        raise ValueError("Name must be 2 to 60 characters long.")
    for character in name:
        if not character.isalpha() and character not in NAME_SYMBOLS:
            raise ValueError("Name may contain only letters, spaces, periods, "
                             "hyphens and apostrophes.")
    return name


def validate_phone(phone):
    """
    A Philippine mobile number: 09XXXXXXXXX or +639XXXXXXXXX.
    Spaces and dashes are ignored. Returned as 09XXXXXXXXX.
    """
    phone = validate_required(phone, "Contact number")
    phone = phone.replace(" ", "").replace("-", "")
    if phone.startswith("+63"):
        phone = "0" + phone[3:]
    if len(phone) != 11 or not phone.startswith("09") or not phone.isdigit():
        raise ValueError("Contact number must be a mobile number like "
                         "09171234567 or +639171234567.")
    return phone


def validate_email(email):
    """An optional e-mail address. Returns '' if left blank."""
    email = email.strip()
    if email == "":
        return ""
    if " " in email or email.count("@") != 1:
        raise ValueError("E-mail address is not valid (example: name@example.com).")
    parts = email.split("@")
    if parts[0] == "" or "." not in parts[1] or parts[1].endswith("."):
        raise ValueError("E-mail address is not valid (example: name@example.com).")
    return email.lower()


def validate_date(date_text, today=None):
    """
    A date in YYYY-MM-DD format that is today or later.
    'today' can be given for testing; normally it is the real date.
    """
    date_text = validate_required(date_text, "Date")
    try:
        chosen = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("Date must be a real date in the format YYYY-MM-DD "
                         "(example: 2026-12-15).")
    if today is None:
        today = date.today()
    if chosen < today:
        raise ValueError("The date cannot be in the past.")
    return chosen.strftime("%Y-%m-%d")


def validate_time(time_text):
    """A start time on the hour, from 08:00 to 16:00 (office hours)."""
    time_text = validate_required(time_text, "Time")
    try:
        chosen = datetime.strptime(time_text, "%H:%M")
    except ValueError:
        raise ValueError("Time must use the 24-hour format HH:MM (example: 09:00).")
    if chosen.minute != 0:
        raise ValueError("Appointments start on the hour (example: 09:00, 10:00).")
    if chosen.hour < OPENING_HOUR or chosen.hour > LAST_START_HOUR:
        raise ValueError("Office hours: appointments can start from 08:00 to 16:00.")
    return chosen.strftime("%H:%M")


def validate_amount(amount_text):
    """A peso amount greater than zero with at most two decimal places."""
    amount_text = validate_required(amount_text, "Amount")
    amount_text = amount_text.replace(",", "")
    try:
        amount = float(amount_text)
    except ValueError:
        raise ValueError("Amount must be a number (example: 1500 or 1500.50).")
    if "." in amount_text:
        decimals = amount_text.split(".")[1]
        if len(decimals) > 2:
            raise ValueError("Amount can have at most two decimal places.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    return round(amount, 2)


def validate_menu_number(choice_text, lowest, highest):
    """A whole number between lowest and highest (used for menus)."""
    choice_text = validate_required(choice_text, "Choice")
    if not choice_text.isdigit():
        raise ValueError("Please type a number.")
    number = int(choice_text)
    if number < lowest or number > highest:
        raise ValueError("Please choose a number from " + str(lowest)
                         + " to " + str(highest) + ".")
    return number


def validate_concern(concern):
    """A short description of the client's concern (required, up to 200 characters)."""
    concern = validate_required(concern, "Concern")
    if len(concern) > 200:
        raise ValueError("Please keep the concern to 200 characters or fewer.")
    return concern


def validate_search_text(search_text):
    """Text to search for (required)."""
    return validate_required(search_text, "Search text")
