📘 Retail Management System (Django + DRF)

A full-featured Retail Management System built with Django Rest Framework (DRF).
It supports multi-branch inventory, sales tracking, vendor management, ledger entries, and reporting with role-based permissions.

🚀 Live API

Base URL: https://retailm.pythonanywhere.com/api/

🔹 Authentication

Obtain JWT Access & Refresh Token → https://retailm.pythonanywhere.com/api/token/

(Login with admin credentials to get token)

Example Request:

POST /api/token/
{
  "username": "admin",
  "password": "yourpassword"
}


Response:

{
  "refresh": "your-refresh-token",
  "access": "your-access-token"
}

📂 Features

Branch Management → Create & manage multiple store branches.

Product Management → Track inventory with stock, price, cost, and expiry date.
(Now supports product images 📷)

Vendor Management → Manage supplier details.

Sales & Invoices → Record sales, auto-calculate totals, track payment methods.

Ledger Entries → Financial transactions per branch.

Stock Movement → In/out records for better inventory control.

Audit Log → Track user actions.

User Roles → Admin, Manager, Cashier, Staff with custom permissions.

Reports → Sales reports, low-stock alerts.

🛠️ Tech Stack

Backend: Django 5, Django Rest Framework

Auth: JWT (SimpleJWT)

Database: SQLite (local) / MySQL or PostgreSQL (production)

Hosting: PythonAnywhere

Frontend: React (in progress)

🔐 Roles & Permissions

Admin → Full access

Manager → Manage branch products, vendors, sales

Cashier → Record sales, view products

Staff → Read-only

⚡ Installation (Local Development)

Clone the repo:

git clone https://github.com/yourusername/retailm.git
cd retailm


Create virtual environment & install dependencies:

python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt


Run migrations:

python manage.py migrate


Create superuser:

python manage.py createsuperuser


Run server:

python manage.py runserver

Below is the link to admin panel.

URL : https://retailm.pythonanywhere.com/api/
Username : Owner
Password : owner1122
