# Mughaliyaa Riyawaat — Real Flask Store

A production-ready Flask e-commerce foundation for a Pakistani luxury fashion store.

## Included
- Responsive luxury storefront
- Product catalogue, search and categories
- Product variants, stock and wishlist
- Session cart and checkout
- Customer OTP login using Twilio Verify
- Customer profile and order history
- COD checkout with delivery GPS coordinates
- WhatsApp support/order link
- Admin dashboard for products and orders
- Order status + tracking code
- PostgreSQL-ready database with SQLite local fallback
- Gunicorn production server
- Render deployment blueprint

## Important
The store can run locally with SQLite. For a real public store, use a managed PostgreSQL database and HTTPS. Real SMS OTP requires Twilio Verify credentials. Online card payments are intentionally not presented as active until a real payment gateway is connected.

## Local run
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```
Open `http://127.0.0.1:5000`.

## Production
Use the included `render.yaml` on Render, connect a managed PostgreSQL database, and add the environment variables shown in `.env.example`.

## Admin
Set `ADMIN_PHONE`, `ADMIN_EMAIL` and a strong `ADMIN_PASSWORD`. The admin account is created automatically on first database initialization. Login is still performed through Twilio OTP.
