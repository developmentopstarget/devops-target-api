# DevOps Target — Backend (Django `api`) Build Spec
Commerce backend for `devops-target-api` · v1.0 · powers the `web` frontend screens.

## Context (existing `api`)

Django + DRF + djoser (Token auth) + Channels + OpenAI, live at `backend/`. Apps: `api` (Item, Notification, MeView), `chat` (Message, consumers, websocket). Auth mounted at **`/api/auth/`** (djoser + authtoken). DRF default auth = TokenAuthentication, default permission = IsAuthenticated. Dev DB SQLite; Postgres in prod.

> **Frontend alignment fix:** the `web` auth spec used `/auth/...`; the real prefix is **`/api/auth/...`** (login `POST /api/auth/token/login/`, register `POST /api/auth/users/`, logout `POST /api/auth/token/logout/`, reset `POST /api/auth/users/reset_password/`). Use these in the frontend auth client.

## Goal

Add a `shop` app with the commerce data model + REST API the storefront needs, wire Stripe payments, add 2FA, and extend the profile endpoint — so the frontend stops using placeholder data. Keep the existing branch→PR→CI→merge discipline and Django admin as the management UI.

## New app: `shop`

### Models

- **Category** — `name`, `slug` (unique), `parent` (self-FK, nullable), `image`, `order`, `is_active`.
- **Product** — `name`, `slug` (unique), `category` (FK), `brand`, `description`, `price` (Decimal), `compare_at_price` (Decimal, nullable), `sku` (unique), `stock` (int), `is_active`, `is_featured`, `specs` (JSONField — CPU/RAM/storage/etc.), `created_at`. Derived: `in_stock`, stock status (in/low/out via a `LOW_STOCK_THRESHOLD`).
- **ProductImage** — `product` (FK), `image`/`url`, `alt`, `order`, `is_primary`.
- **Review** — `product` (FK), `user` (FK), `rating` (1–5), `title`, `body`, `created_at`; unique (product, user). Product exposes `aggregate_rating` + `review_count`.
- **Address** — `user` (FK), `full_name`, `line1`, `line2`, `city`, `postal_code`, `phone`, `is_default`, `label`.
- **Order** — `user` (FK, nullable for guest), `number` (unique, human `DT-#####`), `email`, `status` (pending/paid/preparing/ready/shipped/delivered/cancelled/refunded), `fulfillment` (pickup/delivery), `shipping_address` (FK/snapshot JSON), `subtotal`, `discount`, `delivery_fee`, `tax`, `total`, `promo_code`, `stripe_payment_intent`, `created_at`.
- **OrderItem** — `order` (FK), `product` (FK/snapshot), `name`, `sku`, `unit_price`, `quantity`, `line_total`.
- **Wishlist** — `user` (FK), `products` (M2M) — or per-row `WishlistItem`.
- **(Optional) Cart/CartItem** — server cart for logged-in sync; frontend uses localStorage now, so this is **phase-2/optional**. If built: `Cart(user)`, `CartItem(cart, product, quantity)`.
- **(Optional) PromoCode** — `code`, `percent_off`/`amount_off`, `active`, `min_subtotal`, `expires_at`.

Each model: migration, `__str__`, sensible `Meta.ordering`, indexes on `slug`/`sku`/`status`.

### Serializers (DRF)

- `CategorySerializer`, `ProductListSerializer` (light, for grid), `ProductDetailSerializer` (specs, images, aggregate rating, reviews), `ReviewSerializer`, `AddressSerializer`, `OrderSerializer` (+ nested items), `OrderCreateSerializer`, `WishlistSerializer`. Never trust client price/total — recompute server-side on order create.

### Endpoints (mount in `config/urls.py` router under `/api/`)

Public (read):
- `GET /api/products/` — list; filters: `category`, `brand`, `ram`, `storage`, `in_stock`, `min_price`, `max_price`, `search`; ordering: `price`, `-price`, `newest`, `rating`; pagination (page-based, matches `/products` UI). Mirror the URL params the frontend already uses.
- `GET /api/products/{slug}/` — detail (specs, images, rating, reviews).
- `GET /api/categories/`, `GET /api/categories/{slug}/`.
- `GET /api/products/{slug}/reviews/` — list; `POST` (auth) to add.

Auth-gated:
- `GET/PATCH /api/me/` — extend existing MeView: allow updating `first_name`, `email`, and add profile prefs (`language`, `theme`) via a `Profile` model (OneToOne) or user fields.
- `GET/POST/PATCH/DELETE /api/addresses/`.
- `GET /api/orders/`, `GET /api/orders/{id}/`, `POST /api/orders/` (create from posted line items or server cart; recompute totals; decrement stock atomically).
- `GET /api/wishlist/`, add/remove.
- Reuse existing `/api/notifications/` (+ create order/shipping notifications on status change).

Checkout / Stripe:
- `POST /api/checkout/intent/` — validate cart items + stock, compute total server-side, create Stripe **PaymentIntent**, return `client_secret`.
- `POST /api/webhooks/stripe/` — verify signature; on `payment_intent.succeeded` mark order paid, decrement stock, create confirmation notification. (CSRF-exempt, raw body.)

### Permissions

Read endpoints (products/categories/reviews list) = `AllowAny` (override the global IsAuthenticated per-view). Everything user-owned (orders/addresses/wishlist/me) = authenticated + object ownership (users only see their own). Reviews POST = authenticated.

### Django admin (the management UI)

Register Category, Product (+ inline ProductImage), Order (+ inline OrderItem, status actions), Review, Address, PromoCode with good `list_display`, `list_filter`, `search_fields`, `date_hierarchy`, and stock/price columns — mirror the polish already applied to Item/Message admin. This is how the shop is run day-to-day.

## Cross-cutting additions

- **2FA (django-otp):** add `django-otp` + TOTP device; endpoints to enroll (return provisioning URI/QR secret), verify, disable; enforce a second step at login when enabled. Wire to the frontend `/verify-2fa` + account security panel.
- **Chat message type:** add `sender_type` (user/ai/staff) to `chat.Message` so the frontend can distinguish AI vs staff bubbles (+ migration). Update consumer to set it.
- **Profile prefs:** `language` (LTR/RTL locale) + `theme` on a `Profile` model, surfaced via `/api/me/`.
- **Seed command:** `manage.py seed_catalog` to load categories + ~20 products (mirror the frontend placeholder catalog so data matches during integration).
- **Email:** order confirmation + password reset via Django email backend (dev = console backend).
- **Settings/env:** `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` (expose publishable to frontend), `TAX_RATE`, `LOW_STOCK_THRESHOLD`, `DELIVERY_FEE`, `FREE_DELIVERY_THRESHOLD`. Add to `.env.example`. Keep CORS allowing the `web` origin.
- **Deps:** add `stripe`, `django-otp`, `qrcode` to `requirements.txt`.

## Tests

- Product filtering/sorting/search + pagination.
- Order create recomputes totals server-side, decrements stock, rejects out-of-stock/oversell (atomic `select_for_update`).
- Address/order ownership isolation (user A can't read user B's).
- Review uniqueness + auth.
- Stripe intent (mock Stripe) + webhook signature handling (mock).
- 2FA enroll/verify.
- Keep CI green: `backend-tests`, and existing `frontend-build`/`docker-build`.

## Build order (suggested)

1. `shop` app + Category/Product/ProductImage/Review models + migrations + admin + seed command.
2. Product/category/review read endpoints (public) → point the frontend `/products` + `/products/[slug]` at these.
3. Address + extended `/api/me/` (profile prefs) → account profile/addresses.
4. Order + OrderItem + order endpoints → account orders.
5. Stripe intent + webhook → checkout.
6. 2FA (django-otp) → account security + `/verify-2fa`.
7. `sender_type` on chat + email + notifications polish.

---

## Copy-paste prompt for Claude Code (run in the `api` repo)

```
Work in the devops-target-api repo (Django + DRF + djoser + Channels). Build the commerce backend per docs/backend-spec.md. Follow the existing conventions (branch→PR→CI→merge, explicit staging, Django admin polish, tests). Do NOT migrate off Django.

Do it in these increments, each its own commit (or PR) with migrations + tests + admin:
1. Create a `shop` app. Models: Category, Product (price/compare_at_price/sku/stock/specs JSON/is_active/is_featured), ProductImage, Review (unique per user+product; expose aggregate_rating + review_count on Product). Migrations, __str__, Meta ordering, indexes on slug/sku. Register all in Django admin with list_display/list_filter/search_fields/date_hierarchy (match the polish on the existing Item/Message admin). Add a `seed_catalog` management command loading categories + ~20 products that mirror the frontend placeholder catalog.
2. Read endpoints (AllowAny, override global IsAuthenticated per-view), mounted under /api/: GET /api/products/ with filters (category, brand, ram, storage, in_stock, min_price, max_price, search) + ordering (price, -price, newest, rating) + page pagination matching the /products UI params; GET /api/products/{slug}/; GET /api/categories/ + /{slug}/; GET/POST /api/products/{slug}/reviews/ (POST auth-only). Light vs detail serializers.
3. Address model + CRUD /api/addresses/ (owner-scoped). Extend MeView to GET/PATCH first_name/email + a Profile model (language, theme prefs) surfaced via /api/me/.
4. Order + OrderItem models; GET /api/orders/, GET /api/orders/{id}/ (owner-scoped), POST /api/orders/ that recomputes totals SERVER-SIDE from product prices, applies promo/delivery/tax rules, and decrements stock atomically (select_for_update); reject oversell. Create a notification on order + status change (reuse existing Notification).
5. Stripe: add `stripe` dep. POST /api/checkout/intent/ (validate stock, compute total server-side, create PaymentIntent, return client_secret). POST /api/webhooks/stripe/ (CSRF-exempt, verify signature; on payment_intent.succeeded mark order paid + decrement stock + notify). Env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_PUBLISHABLE_KEY, TAX_RATE, DELIVERY_FEE, FREE_DELIVERY_THRESHOLD, LOW_STOCK_THRESHOLD → .env.example.
6. 2FA: add django-otp + qrcode. Endpoints to enroll (return provisioning URI/secret), verify, disable; enforce second step at login when enabled.
7. Add `sender_type` (user/ai/staff) to chat.Message (+ migration; consumer sets it). Order-confirmation email (console backend in dev).

Rules: never trust client-sent prices/totals; owner-scope all user data; keep read endpoints public and everything else authenticated; write tests for filtering, order-total recompute + stock decrement + oversell rejection, ownership isolation, review uniqueness, Stripe intent/webhook (mocked), 2FA. Run `python manage.py makemigrations && migrate && test` and keep CI green. Update handoff.md before stopping. Commit per increment; stage files explicitly (no `git add .`).
```
