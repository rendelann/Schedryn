# Schedryn — System Flow, Architecture and Design System

**System:** Schedryn — Law Office Appointment and Legal Fee Management System
**Platform:** Python 3 desktop application (Tkinter + ttk, SQLite)

---

## Contents

1. [System Flow](#1-system-flow)
2. [Architectural Structure](#2-architectural-structure)
3. [Design System](#3-design-system)

---

# 1. System Flow

## 1.1 Overall Flow

```text
              ┌──────────────────┐
              │   python main.py │
              └────────┬─────────┘
                       ▼
          ┌─────────────────────────┐
          │ Prepare the database     │  create the 6 tables if they
          │ (database.py)            │  do not exist yet
          └────────────┬────────────┘
                       ▼
               ◇ Database opened? ◇── No ──► [Show error message] ──► END
                       │ Yes
                       ▼
               ◇ Account exists? ◇
                 │ No          │ Yes
                 ▼             ▼
        [Create Account]   [Log In] ── 5 wrong tries ──► program closes
                 │             │
                 └──────┬──────┘
                        ▼
               ┌────────────────┐
               │   DASHBOARD    │◄───────────────────────────┐
               └───────┬────────┘                            │
                       ▼  (sidebar menu)                     │
    ┌──────────────────┼───────────────────┬───────────────┐ │
    ▼                  ▼                   ▼               ▼ │
 APPOINTMENT       TRANSACTION          REPORTS        ACCOUNT│
 MANAGEMENT        MANAGEMENT                          Change │
 • Appointments    • Record payment     • Collections  password│
 • Clients         • Payment summary    • Unpaid fees  Log out │
 • Legal Services  • Payment history    • Client       Exit    │
 • Notarial        • Save receipt         summary             │
   Register                             • Notarial acts       │
    │                  │                   │                  │
    └──────────────────┴───────────────────┴──────────────────┘
                 every page can return to the Dashboard
```

## 1.2 How One Action Travels Through the System

Every button follows the same path. The screen never touches the database directly.

```text
 USER types and clicks
        │
        ▼
 gui.py ───────────── reads the form fields (.get())
        │
        ▼
 Manager module ───── e.g. appointment_manager.create_appointment()
        │   ├── validators.py ─── checks the input (date, time, phone, money…)
        │   ├── business rules ── overlap, conflict of interest, balance…
        │   └── database.py ───── opens a connection (foreign keys ON)
        │
        ▼
 SQLite database ──── saves inside one locked transaction (BEGIN IMMEDIATE)
        │
        ▼
 Result goes back up:
   success → gui.py refreshes the table and shows a message in the status bar
   rule broken (ValueError) → gui.py shows a warning; nothing is saved
   database problem (sqlite3.Error) → gui.py shows an error; nothing is saved
```

## 1.3 Booking an Appointment

```text
 START
   ▼
 Select CLIENT and LEGAL SERVICE
   ▼
 Enter LEGAL MATTER (required) and ADVERSE PARTY (optional)
   ▼
 Enter DATE (YYYY-MM-DD) and START TIME (HH:MM)
   ▼
 ◇ Conflict of interest? ◇── Yes ─► Warning: adverse party is a client,
   │ No                              or this client was an adverse party
   │                                 ◇ Lawyer proceeds? ◇── No ─► STOP
   │                                        │ Yes
   │                                        ▼
   │                              conflict check = "Acknowledged"
   ▼ conflict check = "Clear"               │
   ◄────────────────────────────────────────┘
   ▼
 Validate: real date, valid time, client exists, service active
   ▼
 End time = start time + service duration
   ▼
 ◇ Ends after midnight? ◇── Yes ─► "Overnight appointments are not supported" ─► STOP
   │ No
   ▼
 ◇ Overlaps a Pending or Confirmed appointment? ◇── Yes ─► "Time slot already taken" ─► STOP
   │ No   (back-to-back is allowed; cancelled slots are free)
   ▼
 Create reference APT-YYYYMMDD-NNNN
   ▼
 Save with status "Pending", fee and duration copied from the service
   ▼
 Show "Appointment booked" ─► END
```

## 1.4 Recording a Legal Fee Payment

```text
 START
   ▼
 Select APPOINTMENT ─► the summary shows professional fee, total paid,
   ▼                   balance, payment status, appointment status
 Enter AMOUNT, choose METHOD (Cash, Check, Bank Transfer, E-Wallet),
 enter OR NUMBER and optional notes
   ▼
 ◇ Amount valid and above zero? ◇── No ─► error ─► STOP
   ▼ Yes
 ◇ OR number filled in and never used before? ◇── No ─► error ─► STOP
   ▼ Yes
 ◇ Appointment cancelled? ◇── Yes ─► error ─► STOP
   ▼ No
 ◇ Amount more than the balance? ◇── Yes ─► error ─► STOP
   ▼ No
 Save payment
   ▼
 Recalculate: total paid, balance, payment status
   ▼
 Offer to save an Acknowledgment Receipt (text file)
   ▼
 END
```

## 1.5 Recording a Notarial Act

```text
 START
   ▼
 Enter Book No. / Series ─► [Next Doc. No.] suggests the next number
   ▼
 Enter Page No., Doc. No., date, time, notarial act, document title,
 principals' names and addresses, identity (personally known OR competent
 evidence), witnesses, fee, place, linked appointment, remarks
   ▼
 Confirm: "Entries cannot be changed or deleted afterwards"
   ▼
 ◇ Doc. No. already used in this Book and Series? ◇── Yes ─► error ─► STOP
 ◇ Date in the future or outside the Series year? ◇── Yes ─► error ─► STOP
 ◇ No ID evidence and not personally known?       ◇── Yes ─► error ─► STOP
 ◇ Linked appointment missing or cancelled?       ◇── Yes ─► error ─► STOP
   ▼ all No
 Save entry (permanent: the database blocks any change or deletion)
   ▼
 END
```

## 1.6 Logging In

```text
 START ─► ◇ Account exists? ◇
            │ No                                  │ Yes
            ▼                                     ▼
   Enter username, password,             Enter username and password
   confirm password                               ▼
            ▼                             ◇ Correct? ◇── Yes ─► Dashboard
   ◇ Username 3–30 chars?    ◇                    │ No
   ◇ Password 8+ chars,      ◇                    ▼
   ◇ letter and number?      ◇           attempts = attempts + 1
   ◇ Passwords match?        ◇                    ▼
            │ all Yes                    ◇ attempts = 5? ◇── Yes ─► program closes
            ▼                                     │ No
   Salt + hash the password                       ▼
   (PBKDF2-SHA256), save                 "Incorrect… N attempt(s) left"
            ▼
        Dashboard
```

## 1.7 Status Lifecycles

**Appointment status** (changed by the lawyer):

```text
              ┌──────────── Cancel ────────────┐
              │                                ▼
  [Pending] ──┴── Confirm ──► [Confirmed] ──┬──► [Cancelled]   (slot freed;
                                            │                   no payments)
                                            └── Complete ──► [Completed]

  Completed and Cancelled are final: no further changes.
  Only Pending and Confirmed appointments block a time slot and can be rescheduled.
```

**Payment status** (calculated automatically, never typed):

| Total paid | Payment status |
|---|---|
| ₱0.00 | Unpaid |
| More than ₱0, less than the fee | Partially Paid |
| Equal to the fee | Paid |

Appointment status and payment status are separate: an appointment can be *Confirmed* and *Unpaid* at the same time.

---

# 2. Architectural Structure

## 2.1 Layered Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                       PRESENTATION LAYER                         │
│  gui.py — LoginWindow, SchedrynApp (sidebar, header, status bar) │
│  Pages: Dashboard · Appointment Management · Transaction         │
│         Management · Reports                                     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ calls functions; never runs SQL
┌───────────────────────────────▼─────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                         │
│  ┌──────────────── MAIN SYSTEM ────────────────┐                 │
│  │ auth_manager.py (login)   reports.py         │                 │
│  └──────────────────────────────────────────────┘                 │
│  ┌── SUBSYSTEM 1: APPOINTMENT MGMT ──┐ ┌─ SUBSYSTEM 2: TRANSACTION ─┐│
│  │ service_manager.py                │ │ transaction_manager.py     ││
│  │ client_manager.py                 │ │ receipt_manager.py         ││
│  │ appointment_manager.py            │ └────────────────────────────┘│
│  │ notarial_register_manager.py      │                               │
│  └───────────────────────────────────┘                               │
└───────────────────────────────┬─────────────────────────────────┘
                                │ every input is checked first
┌───────────────────────────────▼─────────────────────────────────┐
│                VALIDATION LAYER — validators.py                  │
└───────────────────────────────┬─────────────────────────────────┘
┌───────────────────────────────▼─────────────────────────────────┐
│               DATA ACCESS LAYER — database.py                    │
│   connections (foreign keys ON) · table creation · helpers        │
└───────────────────────────────┬─────────────────────────────────┘
┌───────────────────────────────▼─────────────────────────────────┐
│                SQLITE DATABASE — data/schedryn.db                │
└─────────────────────────────────────────────────────────────────┘
        Generated files: receipts/*.txt  ·  reports/*.txt
```

## 2.2 Modules and Responsibilities

| Part | Module | Responsibility |
|---|---|---|
| Main System | `main.py` | Starts the program: prepares the database, opens the window |
| Main System | `gui.py` | All screens, forms, tables, messages and navigation |
| Main System | `database.py` | Connections, the six tables, triggers, shared helpers |
| Main System | `validators.py` | Checks dates, times, phone numbers, e-mail, money, OR numbers |
| Main System | `auth_manager.py` | Account creation, login, password change |
| Main System | `reports.py` | Collections, Unpaid Fees, Client Summary, Notarial Acts |
| Subsystem 1 | `service_manager.py` | Legal services, categories, fees, activation |
| Subsystem 1 | `client_manager.py` | Client records and appointment history |
| Subsystem 1 | `appointment_manager.py` | Booking, overlaps, conflict of interest, rescheduling, status |
| Subsystem 1 | `notarial_register_manager.py` | Permanent notarial register entries |
| Subsystem 2 | `transaction_manager.py` | Payments, balances, payment status, daily totals |
| Subsystem 2 | `receipt_manager.py` | Acknowledgment receipts (text files) |
| Tests | `tests/` (10 files) | Automated tests, run without opening the window |

## 2.3 Dependency Rules

```text
 main.py ──► database.py
    └──────► gui.py ──► auth_manager, reports,
                         appointment_system/*, transaction_system/*
                                  │
                                  ▼
                         validators.py ──► (no project imports)
                         database.py   ──► (no project imports)
```

1. `gui.py` may call any manager; managers never import `gui.py` or Tkinter.
2. Only the managers and `database.py` contain SQL.
3. `database.py` and `validators.py` depend on nothing else in the project.
4. Both subsystems share one database; they do not call each other's screens.
5. The Main System joins the subsystems (for example, the dashboard shows appointments from Subsystem 1 with balances from Subsystem 2).

## 2.4 Database Design

```text
┌──────────────┐        ┌──────────────────────┐        ┌──────────────────┐
│   services   │1      *│     appointments     │1      *│   transactions   │
│──────────────│────────│──────────────────────│────────│──────────────────│
│ service_id PK│        │ appointment_id PK     │        │ transaction_id PK│
│ name (unique)│        │ appointment_reference │        │ appointment_id FK│
│ category     │        │ client_id FK          │        │ amount_centavos  │
│ price_centavos│       │ service_id FK         │        │ receipt_number   │
│ duration_min │        │ date, start, end      │        │   (unique)       │
│ status       │        │ fee + duration        │        │ payment_method   │
└──────────────┘        │   snapshots           │        │ payment_date     │
                        │ status                │        └──────────────────┘
┌──────────────┐        │ legal_matter          │
│   clients    │1      *│ adverse_party         │1      *┌──────────────────┐
│──────────────│────────│ conflict_check        │────────│ notarial_register│
│ client_id PK │        └──────────────────────┘ (optional)──────────────────│
│ name         │                                          │ entry_id PK      │
│ client_type  │        ┌──────────────────────┐          │ doc/page/book no.│
│ contact      │        │      accounts        │          │ series_year      │
│ email        │        │──────────────────────│          │ act, title       │
│ address      │        │ account_id PK        │          │ principals       │
└──────────────┘        │ username (unique)    │          │ identity, fee    │
                        │ password_hash, salt  │          │ appointment_id FK│
                        └──────────────────────┘          └──────────────────┘
```

**Safeguards in the database:**

| Safeguard | Purpose |
|---|---|
| Foreign keys with `ON DELETE RESTRICT` | A client, service or appointment in use cannot be deleted |
| `CHECK` rules | Fees, durations and amounts above zero; only approved statuses, categories, types and methods |
| `UNIQUE` | Service names, appointment references, OR numbers, usernames, Doc. No. per Book and Series |
| Triggers `stop_notarial_update` / `stop_notarial_delete` | Notarial entries are permanent |
| Snapshots of fee and duration | Changing a service never changes past appointments |
| Money in whole centavos | No decimal rounding errors (₱1,500.50 is stored as 150050) |
| `BEGIN IMMEDIATE` transactions | The check and the save happen together; two entries cannot slip in at once |

## 2.5 Error-Handling Model

| Error type | Raised by | What the user sees | Saved? |
|---|---|---|---|
| `ValueError` (invalid input or broken rule) | validators, managers | Yellow warning with a plain message | No |
| `sqlite3.Error` (database problem) | database / managers | Red error with details | No (rolled back) |
| `OSError` (file problem: receipts, reports) | receipt and report modules | Error message | Record kept; file not created |
| Database cannot be opened at start | `main.py` | Error window, program stops | — |

## 2.6 Folder Structure

```text
Schedryn/
├── main.py                     Main System — start here
├── gui.py                      Presentation layer
├── database.py                 Data access layer
├── validators.py               Validation layer
├── auth_manager.py             Login and passwords
├── reports.py                  Reports
├── appointment_system/         Subsystem 1
│   ├── service_manager.py
│   ├── client_manager.py
│   ├── appointment_manager.py
│   └── notarial_register_manager.py
├── transaction_system/         Subsystem 2
│   ├── transaction_manager.py
│   └── receipt_manager.py
├── tests/                      Automated tests (10 files)
├── data/schedryn.db            Database (created on first run)
├── receipts/                   Saved receipts (created when needed)
├── reports/                    Saved reports (created when needed)
└── Schedryn_Project_Plan.md    Project plan
```

---

# 3. Design System

## 3.1 Design Principles

1. **Professional and calm:** a navy-and-gold palette suited to a law office.
2. **Clear status at a glance:** colour-coded statuses, always paired with a text label.
3. **Prevent mistakes before they happen:** checks on every field, confirmations for permanent actions, plain-language messages.
4. **Fits a laptop:** every screen works on a 1366 × 768 display.
5. **Consistent:** the same colours, fonts, buttons and tables on every page.

## 3.2 Colour Palette

| Token | Hex | Used for |
|---|---|---|
| `NAVY` | `#14213D` | Sidebar, table headings, logo, login brand panel |
| `NAVY_LIGHT` | `#22335C` | Active sidebar item, dividers |
| `NAVY_HOVER` | `#1B2A4B` | Sidebar item under the mouse |
| `GOLD` | `#C9A227` | Logo "S", active-page marker, today's bar in the chart |
| `ACCENT` | `#1F4E9C` | Primary buttons, focused text boxes, signed-in user |
| `ACCENT_DARK` | `#173B77` | Primary button when pressed |
| `DANGER` | `#C0392B` | "Cancel Appointment" button, Unpaid Legal Fees card |
| `WHITE` | `#FFFFFF` | Header, cards, tables, text boxes |
| `BACKGROUND` | `#F3F4F8` | Page background |
| `BORDER` | `#D9DDE7` | Card, panel and table borders |
| `TEXT_DARK` | `#1A202C` | Main text |
| `TEXT_MUTED` | `#6B7280` | Captions, hints, dates, status bar |

## 3.3 Status Colours

| Appointment status | Text colour | Hex |
|---|---|---|
| Pending | Amber | `#B7791F` |
| Confirmed | Blue | `#1F4E9C` |
| Completed | Green | `#2F855A` |
| Cancelled | Grey | `#9CA3AF` |

The status word is always shown in its own column, so the meaning does not depend on colour alone.

## 3.4 Typography

**Typeface:** Segoe UI on Windows; the system default elsewhere.

| Role | Size | Weight | Example |
|---|---:|---|---|
| Login brand | 20 | Bold | "SCHEDRYN" on the login panel |
| Card value | 20 | Bold | "₱1,500.00" |
| Page title | 16 | Bold | "Dashboard" in the header |
| Login heading | 16 | Bold | "Welcome back" |
| Greeting | 15 | Bold | "Good afternoon, atty.nat" |
| Sidebar brand | 14 | Bold | "SCHEDRYN" |
| Section heading | 11 | Bold | "Today's Schedule" |
| Form group title | 10 | Bold | "New Appointment" |
| Body and menu text | 10 | Regular | Form labels, sidebar items |
| Table heading | 9 | Bold | "Legal Matter" |
| Small text | 9 | Regular | Header date, status bar, lower sidebar buttons |
| Caption | 8 | Bold | "COLLECTED TODAY" on cards |
| Hint | 8 | Regular | "Date: YYYY-MM-DD   Time: HH:MM (24-hour)" |

## 3.5 Layout and Spacing

```text
┌────────────┬──────────────────────────────────────────────────────┐
│            │ HEADER  Page title                 Date · Signed in  │
│  SIDEBAR   ├──────────────────────────────────────────────────────┤
│  230 px    │                                                      │
│            │  CONTENT                                             │
│  Logo      │  Form panel (left)   │   Search bar + table (right)  │
│  Menu      │                      │                               │
│            │                                                      │
│  Account   ├──────────────────────────────────────────────────────┤
│  buttons   │ STATUS BAR  last action message                      │
└────────────┴──────────────────────────────────────────────────────┘
```

| Item | Value |
|---|---|
| Default window | 1360 × 780 (opens maximized on Windows) |
| Minimum window | 1100 × 640 |
| Target screen | 1366 × 768 laptop |
| Sidebar width | 230 px, full height |
| Header padding | 24 px left/right, 12 px top/bottom |
| Page padding | 12 px |
| Table row height | 26 px |
| Button padding | 10 px × 5 px |
| Tab padding | 14 px × 6 px |
| Space between cards | 10 px |
| Chart size | 340 × 300 px |

**Page pattern:** most management screens put the **form on the left** and the **search bar and table on the right**, so the user enters data and sees the result side by side.

## 3.6 Components

**Sidebar**
- Navy background with the logo (gold "S" in a gold-outlined square), "SCHEDRYN" and "Law Office".
- Menu items: Dashboard, Appointment Management, Transaction Management, Reports.
- The **open page** has a lighter navy background and a **4 px gold marker** on its left edge.
- Items change shade when the mouse is over them.
- Bottom group: Change Password, Log Out, and Exit (Exit in light red).

**Header**
- White bar: page title on the left, today's date and "Signed in as …" on the right.

**Summary cards (Dashboard)**
- White card, 1 px border, a **5 px coloured stripe** on the left, uppercase caption, large coloured value.
- Five cards: Today's Appointments (navy), Pending (amber), Confirmed (blue), Collected Today (green), Unpaid Legal Fees (red).

**Collections chart (Dashboard)**
- Bar chart of the last 7 days; **today's bar in gold**, earlier days in navy.
- Short amounts above bars (₱1.5k), day and date below, 7-day total at the top.

**Tables**
- Navy heading row with white bold text.
- Striped rows (white / `#F7F8FB`); selected row light blue (`#D6E2F7`).
- Status text coloured by status; vertical and horizontal scroll bars.

**Buttons**

| Type | Look | Used for |
|---|---|---|
| Primary | Blue fill, white bold text | Main action: Create Appointment, Record Payment, Save Entry, Log In |
| Secondary | White with grey border | Clear, Search, Show All, Refresh, Save Receipt |
| Danger | White with red text and border | Cancel Appointment |

**Forms**
- Label on the left, text box on the right; required fields marked with `*`.
- Text boxes: white, grey border, **blue border when selected**.
- Drop-down lists (read-only) for choices: client, service, status, category, method.
- Hints in small grey text under the fields that need a format.
- Related short fields side by side (Book No. / Series, Page No. / Doc. No., Date / Time).

**Tabs (Appointment Management)**
- Appointments · Clients · Legal Services · Notarial Register.
- Selected tab: white with navy text; others: light grey with grey text.

**Login window**
- Two panels: navy brand panel (logo, name, tagline, short gold line) and a white form panel.
- First run shows "Create your account"; later runs show "Welcome back".
- Password characters hidden as dots.

## 3.7 Feedback and Messages

| Situation | How it is shown |
|---|---|
| Invalid input or broken rule | Warning window titled "Please check your input" with a plain explanation |
| Database problem | Error window titled "Database error" |
| Permanent or important action (cancel, complete, notarial entry, log out, exit) | Yes/No confirmation |
| Possible conflict of interest | Warning listing each match; the lawyer chooses whether to continue |
| Successful action | Message in the status bar (and an information window after booking) |
| File saved (receipt, report) | Shows where it was saved; on Windows, offers to open it |

**Message style:** short, plain sentences that say what went wrong and how to fix it, for example *"Date must use the format YYYY-MM-DD (for example 2026-11-20)."*

## 3.8 Accessibility Notes

- Status colours are always paired with the status word.
- Dark text on light backgrounds and white text on navy keep good contrast.
- Every action can be done with clearly labelled buttons; **Enter** submits the login form and runs searches.
- Required fields are marked, and every error names the field to fix.
