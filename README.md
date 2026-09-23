# Mughaliyaa Riyawaat — Full Store

A production-oriented Flask e-commerce starter for a Pakistani luxury fashion brand.

## Included
- Luxury responsive storefront
- Product categories, search, filters, variants, stock
- Product detail pages
- Cart and checkout
- Customer accounts and order history
- Phone OTP architecture using Twilio Verify
- Secure password hashing for optional admin account
- Admin dashboard
- Product/order/customer management
- Coupons
- Wishlist
- Leaflet/OpenStreetMap location picker and delivery map
- Order tracking status and tracking code
- WhatsApp contact/order links
- PostgreSQL-ready database configuration
- Editable store/contact/theme settings

## Important
Real SMS OTP, online payments, WhatsApp automation and email sending require merchant/provider credentials. The project does not contain fake production credentials.

## Run locally
1. Create a virtual environment.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.
4. `python app.py`
5. Open `http://127.0.0.1:5000`

For production, use PostgreSQL, HTTPS, a proper WSGI server, persistent uploads/object storage, backups, and real provider credentials.
