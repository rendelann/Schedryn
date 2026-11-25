"""
file_handler.py - Saving and loading records, so they are kept between runs.

Files used (all inside the program's folder):
- data/appointments.json  appointments, saved as JSON
                          read with "r", rewritten in full with "w"
- data/transactions.csv   payments, one row per payment
                          read with "r", new payments added with "a" (append)
- receipts/<ID>.txt       one receipt per payment, written with "w"
- data/error_log.txt      unexpected errors, added with "a" (append)

"with open(...)" is used every time, so each file is closed automatically,
even if an error happens while reading or writing.

Missing files: the program starts with an empty list.
Damaged files: a damaged appointments file is renamed (kept for checking)
and the program starts fresh; damaged rows in the payments file are skipped.
"""

import csv
import json
import os
from datetime import datetime

import services

# Use the folder where this file is saved, so the program finds its files
# no matter which folder the terminal is in.
BASE_FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(BASE_FOLDER, "data")
RECEIPTS_FOLDER = os.path.join(BASE_FOLDER, "receipts")
APPOINTMENTS_FILE = os.path.join(DATA_FOLDER, "appointments.json")
TRANSACTIONS_FILE = os.path.join(DATA_FOLDER, "transactions.csv")
ERROR_LOG_FILE = os.path.join(DATA_FOLDER, "error_log.txt")

APPOINTMENT_FIELDS = (
    "appointment_id", "client_name", "contact_number", "email", "service_code",
    "service_name", "service_fee", "date", "time", "concern", "status",
)
TRANSACTION_FIELDS = (
    "transaction_id", "appointment_id", "client_name", "service_name",
    "service_fee", "amount_paid", "change_given", "method", "balance_after",
    "paid_on",
)
MONEY_FIELDS = ("service_fee", "amount_paid", "change_given", "balance_after")


def is_valid_appointment(record):
    """True if the record is a dictionary that has every appointment field."""
    if type(record) != dict:
        return False
    for field in APPOINTMENT_FIELDS:
        if field not in record:
            return False
    return True


def load_appointments(file_path=APPOINTMENTS_FILE):
    """
    Read the saved appointments.
    Returns a TUPLE: (list of appointments, warning message or "").
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return [], ""
    except json.JSONDecodeError:
        backup = file_path + ".damaged"
        os.replace(file_path, backup)
        return [], ("The appointments file was damaged. It was renamed to "
                    + os.path.basename(backup) + " and a new list was started.")

    if type(data) != list:
        backup = file_path + ".damaged"
        os.replace(file_path, backup)
        return [], ("The appointments file had the wrong format. It was renamed to "
                    + os.path.basename(backup) + " and a new list was started.")

    appointments = []
    skipped = 0
    for record in data:
        if is_valid_appointment(record):
            appointments.append(record)
        else:
            skipped = skipped + 1

    warning = ""
    if skipped > 0:
        warning = str(skipped) + " damaged appointment record(s) were skipped."
    return appointments, warning


def save_appointments(appointments, file_path=APPOINTMENTS_FILE):
    """Write all appointments to the JSON file (replaces the old file)."""
    folder = os.path.dirname(file_path)
    os.makedirs(folder, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(appointments, file, indent=2)


def load_transactions(file_path=TRANSACTIONS_FILE):
    """
    Read the saved payments from the CSV file.
    Returns a TUPLE: (list of transactions, warning message or "").
    Rows that cannot be read (for example, a letter where a number should
    be) are skipped and counted.
    """
    transactions = []
    skipped = 0
    try:
        with open(file_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    for field in TRANSACTION_FIELDS:
                        if row[field] is None:
                            raise ValueError("missing value")
                    for field in MONEY_FIELDS:
                        row[field] = float(row[field])
                    transactions.append(row)
                except (KeyError, ValueError):
                    skipped = skipped + 1
    except FileNotFoundError:
        return [], ""

    warning = ""
    if skipped > 0:
        warning = str(skipped) + " damaged payment record(s) were skipped."
    return transactions, warning


def append_transaction(transaction, file_path=TRANSACTIONS_FILE):
    """Add one payment to the end of the CSV file (append mode "a")."""
    folder = os.path.dirname(file_path)
    os.makedirs(folder, exist_ok=True)
    is_new_file = not os.path.exists(file_path) or os.path.getsize(file_path) == 0

    with open(file_path, "a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=TRANSACTION_FIELDS)
        if is_new_file:
            writer.writeheader()
        writer.writerow(transaction)


def save_receipt(transaction, appointment, folder=RECEIPTS_FOLDER):
    """Write a receipt for one payment as a text file. Returns the file path."""
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, transaction["transaction_id"] + ".txt")

    lines = [
        "========================================",
        "        LEGAL MANAGEMENT SYSTEM",
        "          ACKNOWLEDGMENT RECEIPT",
        "========================================",
        "Receipt No.   : " + transaction["transaction_id"],
        "Date paid     : " + transaction["paid_on"],
        "Client        : " + transaction["client_name"],
        "Appointment   : " + appointment["appointment_id"]
        + " (" + appointment["date"] + " " + appointment["time"] + ")",
        "Legal service : " + transaction["service_name"],
        "Service fee   : " + services.format_money(transaction["service_fee"]),
        "Amount paid   : " + services.format_money(transaction["amount_paid"]),
        "Change        : " + services.format_money(transaction["change_given"]),
        "Balance left  : " + services.format_money(transaction["balance_after"]),
        "Paid by       : " + transaction["method"],
        "========================================",
    ]
    with open(file_path, "w", encoding="utf-8") as file:
        for line in lines:
            file.write(line + "\n")
    return file_path


def log_error(error, file_path=ERROR_LOG_FILE):
    """Add an unexpected error to the error log (append mode "a")."""
    folder = os.path.dirname(file_path)
    os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(stamp + "  " + type(error).__name__ + ": " + str(error) + "\n")
