# Bank Management System (Django)

**M.Sc. (CS) – I Sem – 2025-26 | Subject: Python & Django Project**
**Guided by:** Dr. Manisha M. Patil
**Submitted by:** Shreya Vavale (Roll No: 77)

A web-based Bank Management System built with **Python, Django and Django REST Framework**. It manages customers, bank accounts, deposits, withdrawals and transactions through a clean, responsive Bootstrap interface and a REST API.

## Features
- Admin login / logout with Django authentication and CSRF protection
- Dashboard: total customers, accounts, deposits, withdrawals, active/inactive accounts, recent transactions
- Customer CRUD with search
- Bank accounts (Savings / Current) with an auto-generated unique 12-digit account number, activate / deactivate
- Deposit and withdrawal with balance check (withdrawal is blocked when the balance is insufficient)
- Full transaction history with "balance after transaction", filters and pagination
- Delete confirmation popup, success / error messages
- REST API for customers, accounts, deposits, withdrawals and transactions

## Tech Stack
Python 3.10+ · Django · Django REST Framework · SQLite (MySQL optional) · HTML5 · CSS3 · Bootstrap 5

## Installation
```bash
# 1. Go to the project folder
cd bank_management_system

# 2. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the database tables
python manage.py makemigrations bank
python manage.py migrate

# 5. Load demo data (also creates the admin user)
python manage.py load_sample_data

# 6. Run the server
python manage.py runserver
```
Open **http://127.0.0.1:8000/** and log in with **admin / admin123**.
To create your own admin instead: `python manage.py createsuperuser`.

> The pages load Bootstrap from a CDN, so an internet connection is needed for the styling.

## Using MySQL (optional)
1. `pip install mysqlclient` and create a database: `CREATE DATABASE bank_db;`
2. In `bank_project/settings.py` comment out the SQLite block and un-comment the MySQL block.
3. Re-run `migrate`.

## Project Structure
```
bank_management_system/
├── manage.py
├── requirements.txt
├── README.md
├── bank_project/        settings.py, urls.py, wsgi.py, asgi.py
├── bank/                models.py, views.py, forms.py, serializers.py, admin.py, urls.py
│   └── management/commands/load_sample_data.py
├── templates/bank/      base, login, dashboard, customer_*, account_*, money_form, transaction_list, confirm_delete, api_docs
└── static/              css/style.css, js/main.js
```

## Web URLs
| URL | Page |
|---|---|
| `/login/` | Login |
| `/` | Dashboard |
| `/customers/`, `/customers/add/`, `/customers/<id>/`, `/customers/<id>/edit/`, `/customers/<id>/delete/` | Customer pages |
| `/accounts/`, `/accounts/create/`, `/accounts/<no>/`, `/accounts/<no>/edit/`, `/accounts/<no>/delete/` | Account pages |
| `/deposit/`, `/withdraw/`, `/transactions/` | Money operations and history |
| `/api-docs/` | REST API documentation page |
| `/django-admin/` | Django admin site |

## REST API
| Endpoint | Methods |
|---|---|
| `/api/customers/` | GET, POST, PUT, PATCH, DELETE |
| `/api/accounts/` | GET, POST, PUT, PATCH, DELETE |
| `/api/deposits/` | GET, POST (`account`, `amount`) |
| `/api/withdrawals/` | GET, POST (`account`, `amount`) |
| `/api/transactions/` | GET (read-only ledger) |

```bash
curl -u admin:admin123 -X POST http://127.0.0.1:8000/api/deposits/ \
     -H "Content-Type: application/json" \
     -d '{"account": "<account_number>", "amount": "2500.00"}'
```

## Design Notes (useful for viva)
- **Models:** `Customer` → (1 to many) → `BankAccount` → (1 to many) → `Transaction`.
- Deposit / withdraw logic lives in the `BankAccount` model and runs inside `transaction.atomic()`, so the web pages and the API share the same rules.
- Balance is never edited directly; it changes only through a transaction, which keeps the ledger consistent.
- Transactions are read-only in the API so that history cannot be tampered with.
