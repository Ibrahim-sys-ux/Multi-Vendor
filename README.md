# Multi-Vendor

A multi-vendor e-commerce marketplace built with **Django**, supporting three roles in a single app: **Customers**, **Vendors (shops)**, and an **Admin**.

## Features

### Customer
- Registration and login
- Browse shops and products
- Search shops
- Add to cart, checkout, and place orders
- View order history and make payments
- Wishlist
- Product reviews (submitted for admin/vendor approval)
- Submit complaints
- Edit profile

### Vendor (Shop)
- Shop registration with photo and license upload (requires admin approval before going live)
- Vendor login
- Manage product catalog (add / edit / delete products)
- View and update incoming orders (delivery status)
- Track deliveries
- View sales revenue and shop reports (total orders, revenue, best-selling products)
- Moderate reviews left on their products
- Edit shop profile

### Admin
- Approve, reject, or delete vendor registrations
- Manage product categories
- Manage all products across shops
- Manage all orders
- Moderate all reviews
- Handle customer complaints
- View submitted contact form messages

## Tech Stack

- **Backend:** Django 5.1
- **Database:** MySQL (configured in `settings.py`)
- **Static files:** WhiteNoise
- **Deployment:** Configured for Vercel (`vercel.json`)

## Project Structure

```
multi_vendor/
├── manage.py
├── requirements.txt
├── multi_vendor/          # Project settings, URLs, WSGI/ASGI
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── vendor/                # Main app (models, views, forms, urls)
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── migrations/
├── template/               # HTML templates
├── static/                 # CSS/JS/static assets
└── media/                  # Uploaded files (vendor photos, licenses, product images)
```

## Data Models

| Model | Purpose |
|---|---|
| `custdata` | Customer accounts |
| `shopdata` | Vendor/shop accounts, including approval status, photo, and license |
| `Category` | Product categories |
| `Product` | Products, linked to a shop |
| `Order` | Customer orders, linked to product and shop |
| `Transaction` | Payment records for orders |
| `Review` | Product reviews, with approval workflow |
| `Complaint` | Customer complaints |
| `Cart` / `Wishlist` | Per-customer cart and wishlist items |
| `Contact` | Messages submitted via the contact form |

## Getting Started

### Prerequisites
- Python 3.12+
- MySQL server running locally (or update `DATABASES` in `settings.py` to match your setup)

### Setup

```bash
# Clone the repository
git clone https://github.com/Ibrahim-sys-ux/Multi-Vendor.git
cd Multi-Vendor/multi_vendor

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create the database
# In MySQL: CREATE DATABASE vendor_db;

# Apply migrations
python manage.py migrate

# Create an admin/staff user if needed
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

### Default Admin Login (built into the app)
The site admin dashboard (separate from Django's own `/admin/`) is accessed via the regular login form using credentials defined in `vendor/views.py`. **Change these before deploying anywhere public.**

## Known Limitations

This project is a functional prototype and has not been hardened for production use:

- Passwords are stored and compared as plain text rather than hashed.
- Admin credentials are hardcoded in the source.
- Many admin/vendor management views do not check that the requester is authenticated or authorized before acting.
- `DEBUG` is enabled and the Django `SECRET_KEY` is committed to the repository.
- `requirements.txt` lists a PostgreSQL driver (`psycopg2-binary`) while `settings.py` is configured for MySQL — reconcile depending on your target database.
- Payments are simulated and are not connected to a real payment gateway.

Before deploying this publicly, address the items above: hash passwords (e.g. with Django's built-in auth/password hashers), move secrets to environment variables, set `DEBUG = False`, restrict `ALLOWED_HOSTS`, and add proper authentication/permission checks to every admin and vendor view.

