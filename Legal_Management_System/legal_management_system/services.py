"""
services.py - The list of legal services offered by the office.

Each service is a TUPLE: (code, name, fee in pesos).
A tuple is used because a service's details are fixed while the program
runs; tuples cannot be changed by accident.

To change the services or their fees, edit LEGAL_SERVICES below.
"""

LEGAL_SERVICES = (
    ("S1", "Legal Consultation", 1500.00),
    ("S2", "Notarization of a Document", 300.00),
    ("S3", "Affidavit Preparation", 1000.00),
    ("S4", "Special Power of Attorney", 1500.00),
    ("S5", "Contract Review", 3000.00),
    ("S6", "Contract Drafting", 5000.00),
    ("S7", "Deed of Sale Preparation", 3500.00),
    ("S8", "Court Appearance", 8000.00),
)


def format_money(amount):
    """Show an amount as pesos, e.g. 1500 -> 'PHP 1,500.00'."""
    return "PHP " + format(amount, ",.2f")


def get_service_by_number(number):
    """
    Return the service tuple for a menu number (1 = first service).
    Raises ValueError if the number is not on the menu.
    """
    if number < 1 or number > len(LEGAL_SERVICES):
        raise ValueError("Please choose a service number from 1 to "
                         + str(len(LEGAL_SERVICES)) + ".")
    return LEGAL_SERVICES[number - 1]


def get_service_by_code(code):
    """Return the service tuple with this code (e.g. 'S1'), or None."""
    for service in LEGAL_SERVICES:
        if service[0] == code:
            return service
    return None


def build_fee_table():
    """
    Build a DICTIONARY that looks up a service's fee by its code:
    {"S1": 1500.0, "S2": 300.0, ...}
    """
    fee_table = {}
    for service in LEGAL_SERVICES:
        code, name, fee = service      # unpack the tuple
        fee_table[code] = fee
    return fee_table
