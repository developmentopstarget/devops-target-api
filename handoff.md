# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend (`../web`).

Current focus: implementing the commerce backend per `docs/backend-spec.md`, in the 7-increment build order at the bottom of that file. Increments 1-5 are done (catalog models/admin/seed, public read endpoints, addresses + profile prefs, orders, Stripe checkout); increments 6-7 (2FA, chat `sender_type`) are not started.

## Current State

- Branch: `main`
- Working tree: clean.
- What works:
  - `shop` app models: `Category`, `Product`, `ProductImage`, `Review`, `Address`, `Order`, `OrderItem` — all migrated, admin-registered (list_display/list_filter/search_fields/date_hierarchy; `ProductImage` inline on `Product`; `OrderItem` inline + status actions on `Order`).
  - `api` app: `Profile` model (OneToOne on `User`, `language`/`theme` prefs).
  - `seed_catalog` management command — idempotent, loads 6 categories + 19 products mirroring the frontend placeholder catalog.
  - Public read API (`AllowAny`): `GET /api/products/` (filters/sort/pagination matching `web/src/lib/products-filter.ts` exactly), `GET /api/products/{slug}/`, `GET /api/categories/` + `/{slug}/`, `GET/POST /api/products/{slug}/reviews/` (POST auth-only, one review per user per product).
  - Auth-gated API: `GET/PATCH /api/me/` (now returns/accepts `first_name`, `email`, `language`, `theme` alongside `id`/`username`/`email`); `GET/POST/PATCH/DELETE /api/addresses/` (owner-scoped, single default per user enforced in `Address.save()`); `GET/POST /api/orders/` + `GET /api/orders/{id}/` (owner-scoped; POST recomputes subtotal/discount/delivery_fee/tax/total server-side, locks product rows with `select_for_update`, decrements stock atomically, rejects unknown/inactive products, oversell, and invalid promo codes; creates a `Notification` on success).
  - Promo codes `SPRING10` (10%) and `WELCOME5` (5%) hardcoded in `shop/serializers.py` (`PROMO_CODES` dict), mirroring the frontend's placeholder list in `web/src/components/commerce/PromoCode.tsx` — no `PromoCode` model yet (still marked optional/phase-2 in the spec).
  - Pricing settings: `TAX_RATE` (0.08), `DELIVERY_FEE` (9.99), `FREE_DELIVERY_THRESHOLD` (99) — env-driven in `config/settings.py`, defaults mirror `web/src/lib/checkout.ts` / `web/src/config/store.ts` so recomputed totals match the frontend's checkout preview.
  - Stripe Checkout (Increment 5):
    - `POST /api/checkout/intent/` takes `order_id` (auth required), validates order is unpaid and not cancelled, creates Stripe `PaymentIntent`, saves `stripe_payment_intent_id` to order, and returns `client_secret`.
    - `POST /api/webhooks/stripe/` (CSRF-exempt, AllowAny), verifies Stripe signature.
      - On `payment_intent.succeeded`, marks order as `paid` and sends a user notification. Does not double-decrement inventory.
      - On `payment_intent.payment_failed` and `payment_intent.canceled`, transitions order status (`failed` / `cancelled`), sends a user notification, and safely replenishes product stock using a row-level database lock (`select_for_update`) to prevent race conditions.
- What is still broken / not started: django-otp 2FA, chat `sender_type`. See increments 6-7 in `docs/backend-spec.md`.
- Latest test/build status: `python manage.py test` → **117 passed** (including mock tests for Stripe payment intent creation, success, failed, and cancelled webhooks, and invalid signature verification). `python manage.py check` clean. `makemigrations --check --dry-run` → no changes detected.

## Files in Flight

None — Increment 5 fully implemented and tested.

## Changed This Session

- **Increment 5** (commit pending):
  - Added `stripe` library dependency to `backend/requirements.txt` and installed in `.venv`.
  - Registered environment variables (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`) in `backend/config/settings.py` and documented in `backend/.env.example`.
  - Updated `shop/models.py` with `pending_payment` and `failed` order states, added `stripe_payment_intent_id` field to `Order` model, and generated/applied database migration.
  - Implemented `CreatePaymentIntentView` and `StripeWebhookView` views in `shop/views.py` with robust database transactions and row-level locks for inventory replenishment.
  - Registered checkout intent and Stripe webhook URLs in `config/urls.py`.
  - Added comprehensive test suite `StripeCheckoutTests` inside `shop/tests.py` covering payment intent creation flow, succeeded/failed/cancelled webhooks, and signature verification failures.

## Failed Attempts

- None.

## Important Context

- Stripe mock keys (`mock_secret_key`, etc.) are configured as defaults in `settings.py` for testing and local runs without a local `.env` setup.

## Next Step

Start increment 6: Add django-otp and qrcode to `requirements.txt`. Implement 2FA enrollment, verification, and disabling endpoints, and enforce a second factor at login if enabled. See `docs/backend-spec.md` increment 6.

## Commands to Run First

```bash
cd backend
./.venv/bin/python manage.py check
./.venv/bin/python manage.py test
```
