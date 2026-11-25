"""
transaction_system.py - Payments for appointments.

The service fee is taken automatically from the appointment (which copied it
from the chosen legal service), so the cashier never types the fee.

Each payment is a DICTIONARY kept in a LIST of transactions.

Rules:
- Payments are allowed only for booked (not cancelled) appointments.
- A client may pay in parts. If the client hands over more than the balance,
  only the balance is recorded and the change is computed.
- A fully paid appointment cannot receive another payment.
"""

from datetime import datetime

import validators

PAYMENT_METHODS = ("Cash", "GCash", "Bank Transfer", "Check")


def get_total_paid(transactions, appointment_id):
    """Add up all payments made for one appointment."""
    total = 0.0
    for transaction in transactions:
        if transaction["appointment_id"] == appointment_id:
            total = total + transaction["amount_paid"]
    return round(total, 2)


def get_balance(appointment, transactions):
    """Service fee minus everything already paid."""
    paid = get_total_paid(transactions, appointment["appointment_id"])
    return round(appointment["service_fee"] - paid, 2)


def get_payment_status(appointment, transactions):
    """'Unpaid', 'Partially Paid' or 'Paid'."""
    paid = get_total_paid(transactions, appointment["appointment_id"])
    if paid == 0:
        return "Unpaid"
    elif paid < appointment["service_fee"]:
        return "Partially Paid"
    else:
        return "Paid"


def generate_transaction_id(transactions):
    """Return the next ID, e.g. 'TXN-0001'."""
    highest = 0
    for transaction in transactions:
        number = int(transaction["transaction_id"].split("-")[1])
        if number > highest:
            highest = number
    return "TXN-" + str(highest + 1).zfill(4)


def record_payment(appointment, transactions, amount_text, method_number, now=None):
    """
    Record a payment for an appointment and add it to the list.
    Returns the new transaction dictionary (it includes the change given).
    Raises ValueError if the payment is not allowed.
    """
    if appointment["status"] == "Cancelled":
        raise ValueError("Payments cannot be made for a cancelled appointment.")

    balance = get_balance(appointment, transactions)
    if balance <= 0:
        raise ValueError("This appointment is already fully paid.")

    amount_received = validators.validate_amount(amount_text)
    if method_number < 1 or method_number > len(PAYMENT_METHODS):
        raise ValueError("Please choose a payment method from the list.")
    method = PAYMENT_METHODS[method_number - 1]

    # Record no more than the balance; anything extra is change.
    if amount_received > balance:
        amount_paid = balance
        change = round(amount_received - balance, 2)
    else:
        amount_paid = amount_received
        change = 0.0

    if now is None:
        now = datetime.now()

    transaction = {
        "transaction_id": generate_transaction_id(transactions),
        "appointment_id": appointment["appointment_id"],
        "client_name": appointment["client_name"],
        "service_name": appointment["service_name"],
        "service_fee": appointment["service_fee"],
        "amount_paid": amount_paid,
        "change_given": change,
        "method": method,
        "balance_after": round(balance - amount_paid, 2),
        "paid_on": now.strftime("%Y-%m-%d %H:%M:%S"),
    }
    transactions.append(transaction)
    return transaction


def get_payment_summary(appointments, transactions):
    """
    Totals for the whole office, returned as a dictionary:
    total_collected, total_unpaid, paid_count, partial_count, unpaid_count.
    Cancelled appointments are left out of the unpaid totals.
    """
    summary = {
        "total_collected": 0.0,
        "total_unpaid": 0.0,
        "paid_count": 0,
        "partial_count": 0,
        "unpaid_count": 0,
    }
    for transaction in transactions:
        summary["total_collected"] = summary["total_collected"] + transaction["amount_paid"]

    for appointment in appointments:
        if appointment["status"] == "Cancelled":
            continue
        status = get_payment_status(appointment, transactions)
        if status == "Paid":
            summary["paid_count"] = summary["paid_count"] + 1
        elif status == "Partially Paid":
            summary["partial_count"] = summary["partial_count"] + 1
        else:
            summary["unpaid_count"] = summary["unpaid_count"] + 1
        summary["total_unpaid"] = summary["total_unpaid"] + get_balance(appointment, transactions)

    summary["total_collected"] = round(summary["total_collected"], 2)
    summary["total_unpaid"] = round(summary["total_unpaid"], 2)
    return summary
