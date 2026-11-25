"""
main.py - Legal Management System (start the program here).

A console program for a small law office:
- Appointment system: a client types their information, chooses the legal
  service they need, and picks a free date and time.
- Transaction system: when a client pays, the service fee is filled in
  automatically from the service they chose.

Run with:  python main.py
"""

import appointment_system
import file_handler
import services
import transaction_system
import validators


# ---------------------------------------------------------------------------
# Small helpers for asking questions
# ---------------------------------------------------------------------------

def ask_until_valid(prompt, check_function):
    """
    Keep asking until the answer passes the check.
    check_function is one of the functions in validators.py; it returns the
    cleaned answer or raises ValueError with a message for the user.
    """
    while True:
        answer = input(prompt)
        try:
            return check_function(answer)
        except ValueError as error:
            print("  ! " + str(error))


def ask_yes_or_no(prompt):
    """Return True for y/yes and False for n/no."""
    while True:
        answer = input(prompt).strip().lower()
        if answer == "y" or answer == "yes":
            return True
        if answer == "n" or answer == "no":
            return False
        print("  ! Please type Y or N.")


def print_title(title):
    print()
    print("=" * 60)
    print(" " + title)
    print("=" * 60)


# ---------------------------------------------------------------------------
# Showing information
# ---------------------------------------------------------------------------

def show_services():
    print("  No.  Legal service                    Fee")
    print("  ---  -------------------------------  ----------------")
    number = 1
    for service in services.LEGAL_SERVICES:
        code, name, fee = service
        print("  " + str(number).rjust(3) + "  " + name.ljust(31) + "  "
              + services.format_money(fee))
        number = number + 1


def show_appointment_table(appointments, transactions):
    if len(appointments) == 0:
        print("  No appointments to show.")
        return
    print("  ID        Client                Service                      "
          "Date        Time   Payment         Status")
    print("  " + "-" * 110)
    for appointment in appointments:
        payment = transaction_system.get_payment_status(appointment, transactions)
        print("  " + appointment["appointment_id"].ljust(9)
              + " " + appointment["client_name"][0:20].ljust(21)
              + " " + appointment["service_name"][0:27].ljust(28)
              + " " + appointment["date"].ljust(11)
              + " " + appointment["time"].ljust(6)
              + " " + payment.ljust(15)
              + " " + appointment["status"])


def show_appointment_details(appointment, transactions):
    balance = transaction_system.get_balance(appointment, transactions)
    paid = transaction_system.get_total_paid(transactions, appointment["appointment_id"])
    print("  Appointment ID : " + appointment["appointment_id"])
    print("  Client         : " + appointment["client_name"])
    print("  Legal service  : " + appointment["service_name"])
    print("  Date and time  : " + appointment["date"] + " " + appointment["time"])
    print("  Status         : " + appointment["status"])
    print("  Service fee    : " + services.format_money(appointment["service_fee"]))
    print("  Paid so far    : " + services.format_money(paid))
    print("  Balance        : " + services.format_money(balance))


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def book_appointment(appointments):
    print_title("BOOK AN APPOINTMENT")
    print("Please enter your information.")
    client_name = ask_until_valid("  Full name: ", validators.validate_name)
    contact_number = ask_until_valid("  Mobile number (e.g. 09171234567): ",
                                     validators.validate_phone)
    email = ask_until_valid("  E-mail (optional, press Enter to skip): ",
                            validators.validate_email)

    print()
    print("Which legal service do you need?")
    show_services()
    while True:
        choice = input("  Service number: ")
        try:
            service_number = validators.validate_menu_number(
                choice, 1, len(services.LEGAL_SERVICES))
            break
        except ValueError as error:
            print("  ! " + str(error))
    code, service_name, fee = services.get_service_by_number(service_number)
    print("  You chose " + service_name + ". Service fee: " + services.format_money(fee))

    print()
    while True:
        date_text = ask_until_valid("  Date (YYYY-MM-DD): ", validators.validate_date)
        free_times = appointment_system.get_available_times(appointments, date_text)
        if len(free_times) > 0:
            break
        print("  ! That date is fully booked. Please choose another date.")
    print("  Available times: " + ", ".join(free_times))

    while True:
        time_text = ask_until_valid("  Time (HH:MM): ", validators.validate_time)
        if time_text in free_times:
            break
        print("  ! That time is already booked. Please choose an available time.")

    concern = ask_until_valid("  Briefly describe your concern: ",
                              validators.validate_concern)

    print()
    print("Please confirm your appointment:")
    print("  " + client_name + " | " + service_name + " | " + date_text + " " + time_text
          + " | Fee: " + services.format_money(fee))
    if not ask_yes_or_no("Book this appointment? (Y/N): "):
        print("Booking cancelled. Nothing was saved.")
        return

    appointment = appointment_system.create_appointment(
        appointments, client_name, contact_number, email, service_number,
        date_text, time_text, concern)
    try:
        file_handler.save_appointments(appointments)
    except OSError as error:
        appointments.remove(appointment)   # keep the list and the file the same
        raise error
    print()
    print("Your appointment is booked. Your appointment ID is "
          + appointment["appointment_id"] + ".")
    print("Please keep this ID; you will need it when you pay.")


def view_appointments(appointments, transactions):
    print_title("ALL APPOINTMENTS")
    show_appointment_table(appointments, transactions)


def search_appointments(appointments, transactions):
    print_title("SEARCH APPOINTMENTS")
    search_text = ask_until_valid("  Client name (or part of it): ",
                                  validators.validate_search_text)
    results = appointment_system.search_by_client(appointments, search_text)
    print("  Found " + str(len(results)) + " appointment(s).")
    show_appointment_table(results, transactions)


def cancel_appointment(appointments, transactions):
    print_title("CANCEL AN APPOINTMENT")
    appointment_id = input("  Appointment ID (e.g. APT-0001): ")
    appointment = appointment_system.find_appointment(appointments, appointment_id)
    if appointment is None:
        print("  ! No appointment found with that ID.")
        return
    show_appointment_details(appointment, transactions)
    if not ask_yes_or_no("Cancel this appointment? (Y/N): "):
        print("Nothing was changed.")
        return
    appointment_system.cancel_appointment(appointments, transactions, appointment_id)
    try:
         file_handler.save_appointments(appointments)
    except OSError as error:
        appointment["status"] = "Booked"   # undo, because it was not saved
        raise error
    print("Appointment " + appointment["appointment_id"] + " has been cancelled.")


def pay_for_appointment(appointments, transactions):
    print_title("PAY FOR AN APPOINTMENT")
    appointment_id = input("  Appointment ID (e.g. APT-0001): ")
    appointment = appointment_system.find_appointment(appointments, appointment_id)
    if appointment is None:
        print("  ! No appointment found with that ID.")
        return

    # The fee comes automatically from the legal service the client chose.
    show_appointment_details(appointment, transactions)
    if appointment["status"] == "Cancelled":
        print("  ! This appointment was cancelled, so it cannot be paid.")
        return
    if transaction_system.get_balance(appointment, transactions) <= 0:
        print("  This appointment is already fully paid.")
        return

    print()
    print("  Payment methods:")
    number = 1
    for method in transaction_system.PAYMENT_METHODS:
        print("    " + str(number) + ". " + method)
        number = number + 1
    while True:
        choice = input("  Payment method number: ")
        try:
            method_number = validators.validate_menu_number(
                choice, 1, len(transaction_system.PAYMENT_METHODS))
            break
        except ValueError as error:
            print("  ! " + str(error))

    while True:
        amount_text = input("  Amount received: ")
        try:
            transaction = transaction_system.record_payment(
                appointment, transactions, amount_text, method_number)
            break
        except ValueError as error:
            print("  ! " + str(error))

    try:
        file_handler.append_transaction(transaction)
    except OSError as error:
        transactions.remove(transaction)   # it was not saved, so undo it
        raise error

    print()
    print("  Payment recorded: " + transaction["transaction_id"])
    print("  Amount paid  : " + services.format_money(transaction["amount_paid"]))
    if transaction["change_given"] > 0:
        print("  Change       : " + services.format_money(transaction["change_given"]))
    print("  Balance left : " + services.format_money(transaction["balance_after"]))
    print("  Status       : "
          + transaction_system.get_payment_status(appointment, transactions))

    try:
        receipt_path = file_handler.save_receipt(transaction, appointment)
        print("  Receipt saved: " + receipt_path)
    except OSError as error:
        # The payment is already saved; only the receipt file failed.
        print("  ! The payment was saved, but the receipt file could not be created.")
        file_handler.log_error(error)


def view_transactions(transactions):
    print_title("PAYMENT HISTORY")
    if len(transactions) == 0:
        print("  No payments recorded yet.")
        return
    print("  ID        Appointment  Client                Amount paid        "
          "Method          Date paid")
    print("  " + "-" * 105)
    for transaction in transactions:
        print("  " + transaction["transaction_id"].ljust(9)
              + " " + transaction["appointment_id"].ljust(12)
              + " " + transaction["client_name"][0:20].ljust(21)
              + " " + services.format_money(transaction["amount_paid"]).ljust(18)
              + " " + transaction["method"].ljust(15)
              + " " + transaction["paid_on"])


def view_summary(appointments, transactions):
    print_title("PAYMENT SUMMARY")
    summary = transaction_system.get_payment_summary(appointments, transactions)
    print("  Total collected        : " + services.format_money(summary["total_collected"]))
    print("  Total unpaid balances  : " + services.format_money(summary["total_unpaid"]))
    print("  Fully paid appointments: " + str(summary["paid_count"]))
    print("  Partially paid         : " + str(summary["partial_count"]))
    print("  Unpaid                 : " + str(summary["unpaid_count"]))


def view_services():
    print_title("LEGAL SERVICES AND FEES")
    show_services()


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------

def show_menu():
    print_title("LEGAL MANAGEMENT SYSTEM")
    print("  APPOINTMENTS")
    print("    1. Book an appointment")
    print("    2. View all appointments")
    print("    3. Search appointments by client name")
    print("    4. Cancel an appointment")
    print("  TRANSACTIONS")
    print("    5. Pay for an appointment")
    print("    6. View Payment History")
    print("    7. Payment summary")
    print("  OTHER")
    print("    8. View legal services and fees")
    print("    0. Exit")


def main():
    # Load saved records. Each load function returns a tuple:
    # (list of records, warning message).
    appointments, warning = file_handler.load_appointments()
    if warning != "":
        print("Warning: " + warning)
    transactions, warning = file_handler.load_transactions()
    if warning != "":
        print("Warning: " + warning)

    while True:
        show_menu()
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                book_appointment(appointments)
            elif choice == "2":
                view_appointments(appointments, transactions)
            elif choice == "3":
                search_appointments(appointments, transactions)
            elif choice == "4":
                cancel_appointment(appointments, transactions)
            elif choice == "5":
                pay_for_appointment(appointments, transactions)
            elif choice == "6":
                view_transactions(transactions)
            elif choice == "7":
                view_summary(appointments, transactions)
            elif choice == "8":
                view_services()
            elif choice == "0":
                print("Thank you. Goodbye!")
                break
            else:
                print("  ! Please choose a number from the menu.")
        except ValueError as error:
            # Invalid input or a broken business rule: tell the user.
            print("  ! " + str(error))
        except OSError as error:
            # A file could not be read or written (e.g. no permission, disk full).
            print("  ! A file could not be saved or read. Nothing was changed.")
            file_handler.log_error(error)
        except Exception as error:
            # A programming mistake we did not expect: log it and keep running.
            print("  ! Something unexpected went wrong. "
                  "The details were written to data/error_log.txt.")
            file_handler.log_error(error)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        print("Program closed. All saved records are kept.")
