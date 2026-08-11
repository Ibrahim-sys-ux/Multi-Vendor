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

### Environment Variables

Passwords and admin credentials are no longer hardcoded. Create a `.env` file in the project root (and make sure it's listed in `.gitignore`) with:

```
ADMIN_EMAIL=admin@gmail.com
ADMIN_PASSWORD_HASH=<generate with make_password(), see below>
DJANGO_SECRET_KEY=<your-secret-key>
DJANGO_DEBUG=False
```

Generate the admin password hash once with:

```bash
python manage.py shell -c "from django.contrib.auth.hashers import make_password; print(make_password('your-real-admin-password'))"
```

### Migrating Existing Accounts

If you have accounts created before password hashing was added, run the one-off migration command to hash any remaining plaintext passwords:

```bash
python manage.py hash_existing_passwords
```

Back up your database before running this. It's safe to run more than once — already-hashed passwords are left untouched.

### Default Admin Login
The site admin dashboard (separate from Django's own `/admin/`) is accessed via the regular login form, using the `ADMIN_EMAIL` / `ADMIN_PASSWORD_HASH` values set in your environment.

## Access Control

Every view in `vendor/views.py` is protected by one of three decorators, defined in `vendor/decorators.py`:

- `@admin_required` — restricted to the logged-in admin session
- `@vendor_required` — restricted to a logged-in vendor; order, product, and review actions are additionally scoped so a vendor can only act on records belonging to their own shop
- `@customer_required` — restricted to a logged-in customer; cart, wishlist, and payment actions are scoped to the logged-in customer's own records

Public browsing routes (shop listings, shop/product detail pages, approved reviews) intentionally remain open with no login required, matching how real marketplaces let visitors browse before signing in.

## Security Status

| Item                                                  | Status                                                           |
| ----------------------------------------------------- | ---------------------------------------------------------------- |
| Passwords hashed on signup, login, and profile update | ✅ Fixed                                                          |
| Admin credentials moved out of source code            | ✅ Fixed — uses environment variables                             |
| Migration path for pre-existing plaintext passwords   | ✅ Available — `hash_existing_passwords` command                  |
| Permission checks on admin/vendor/customer views      | ✅ Fixed — role-based and object-level access control implemented |
| `DEBUG` / `SECRET_KEY` moved to environment variables | ✅ Fixed                                                          |
| Database driver matches configured database           | ✅ Fixed — MySQL configuration and driver are aligned             |
| Real payment gateway integration                      | ❌ Payments are simulated                                         |

## Known Limitations

* Payments are currently simulated and are not connected to a real payment gateway.
* No automated tests are currently implemented; `tests.py` is empty.
* Production deployment requires appropriate `ALLOWED_HOSTS` configuration.
* Uploaded media files require proper storage configuration for production deployment.
* The application is primarily designed as a Django web application and does not currently provide a dedicated REST API.

Before deploying this publicly, address the remaining items above and restrict `ALLOWED_HOSTS`.

## License

No license specified yet — add one if you intend for others to use or contribute to this project.
