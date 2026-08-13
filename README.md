# Multi-Vendor

A multi-vendor e-commerce marketplace built with **Django**, supporting three roles in a single app: **Customers**, **Vendors (shops)**, and an **Admin**.

## Features

### Customer
- Registration and login
- Browse shops and products (no login required)
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
- **Database:** MySQL (via `mysqlclient`)
- **Static files:** WhiteNoise
- **Config management:** python-decouple (environment variables)
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
│   ├── decorators.py       # role-based access control (admin/vendor/customer)
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
- MySQL server running locally (or update your `.env` to match a remote instance)

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
```

### Environment Variables

All secrets and environment-specific values are read from a `.env` file (already excluded via `.gitignore` — never commit this file). Create one in the project root with:

```
DJANGO_SECRET_KEY=<generate one, see below>
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=vendor_db
DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=<your MySQL password>
DB_PORT=3306

ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD_HASH=<generate with make_password(), see below>
```

Generate a fresh Django secret key:
```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Generate the admin password hash:
```bash
python manage.py shell -c "from django.contrib.auth.hashers import make_password; print(make_password('your-real-admin-password'))"
```

### Running the app

```bash
# Apply migrations
python manage.py migrate

# Create an admin/staff user if needed
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

The app will be available at `http://127.0.0.1:8000/`.

### Migrating Existing Accounts

If you have accounts created before password hashing was added, run the one-off migration command to hash any remaining plaintext passwords:

```bash
python manage.py hash_existing_passwords
```

Back up your database before running this. It's safe to run more than once — already-hashed passwords are left untouched.

### Default Admin Login
The site admin dashboard (separate from Django's own `/admin/`) is accessed via the regular login form, using the `ADMIN_EMAIL` / `ADMIN_PASSWORD_HASH` values set in your `.env`.

## Access Control

Every view in `vendor/views.py` is protected by one of three decorators, defined in `vendor/decorators.py`:

- `@admin_required` — restricted to the logged-in admin session
- `@vendor_required` — restricted to a logged-in vendor; order, product, and review actions are additionally scoped so a vendor can only act on records belonging to their own shop
- `@customer_required` — restricted to a logged-in customer; cart, wishlist, and payment actions are scoped to the logged-in customer's own records

Public browsing routes (shop listings, shop/product detail pages, approved reviews) intentionally remain open with no login required, matching how real marketplaces let visitors browse before signing in.

## Security Status

| Item | Status |
|---|---|
| Passwords hashed on signup, login, and profile update | ✅ Fixed |
| Admin credentials moved out of source code | ✅ Fixed |
| Migration path for pre-existing plaintext passwords | ✅ Available (`hash_existing_passwords` command) |
| Permission checks on admin/vendor/customer views | ✅ Fixed — all views gated by role decorators, with object-level ownership checks on orders, products, reviews, cart, wishlist, and payments |
| `SECRET_KEY` / `DEBUG` / `ALLOWED_HOSTS` in environment variables | ✅ Fixed |
| Database credentials in environment variables | ✅ Fixed |
| `requirements.txt` matches configured database | ✅ Fixed (`mysqlclient` for MySQL) |
| Committed virtual environment removed from repo | ✅ Fixed (132MB → 42MB) |
| `.gitignore` configured | ✅ Fixed |
| Real payment gateway integration | ❌ Payments are simulated (`process_payment` marks orders paid without a gateway) |

## Known Limitations

- **Payments are simulated** — `process_payment` marks an order as paid directly, with no integration to a real payment gateway (e.g. Stripe, Razorpay). Fine for demonstration purposes; would need real gateway + webhook integration before handling real transactions.
- **`api/index.py` (Vercel entry point) has a broken import** — it imports from `myproject.wsgi`, but the actual project package is `multi_vendor`. Fix before attempting a Vercel deployment.
- **No automated tests** — `tests.py` exists but is currently empty.
- **Old `SECRET_KEY` remains in git history** — the exposed key was rotated, but the previous value is still visible in earlier commits. Not in active use, but full removal would require rewriting git history.

## License

No license specified yet — add one if you intend for others to use or contribute to this project.
