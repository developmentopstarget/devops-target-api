# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend (`../web`).

Current focus: implementing the commerce backend per `docs/backend-spec.md`, in the 7-increment build order at the bottom of that file. Increments 1-4 are done (catalog models/admin/seed, public read endpoints, addresses + profile prefs, orders); increments 5-7 (Stripe checkout, 2FA, chat `sender_type`) are not started.

## Current State

- Branch: `main` (local commits ahead of last known origin sync — not pushed this session).
- Working tree: clean.
- What works:
  - `shop` app models: `Category`, `Product`, `ProductImage`, `Review`, `Address`, `Order`, `OrderItem` — all migrated, admin-registered (list_display/list_filter/search_fields/date_hierarchy; `ProductImage` inline on `Product`; `OrderItem` inline + status actions on `Order`).
  - `api` app: `Profile` model (OneToOne on `User`, `language`/`theme` prefs).
  - `seed_catalog` management command — idempotent, loads 6 categories + 19 products mirroring the frontend placeholder catalog.
  - Public read API (`AllowAny`): `GET /api/products/` (filters/sort/pagination matching `web/src/lib/products-filter.ts` exactly), `GET /api/products/{slug}/`, `GET /api/categories/` + `/{slug}/`, `GET/POST /api/products/{slug}/reviews/` (POST auth-only, one review per user per product).
  - Auth-gated API: `GET/PATCH /api/me/` (now returns/accepts `first_name`, `email`, `language`, `theme` alongside `id`/`username`/`email`); `GET/POST/PATCH/DELETE /api/addresses/` (owner-scoped, single default per user enforced in `Address.save()`); `GET/POST /api/orders/` + `GET /api/orders/{id}/` (owner-scoped; POST recomputes subtotal/discount/delivery_fee/tax/total server-side, locks product rows with `select_for_update`, decrements stock atomically, rejects unknown/inactive products, oversell, and invalid promo codes; creates a `Notification` on success).
  - Promo codes `SPRING10` (10%) and `WELCOME5` (5%) hardcoded in `shop/serializers.py` (`PROMO_CODES` dict), mirroring the frontend's placeholder list in `web/src/components/commerce/PromoCode.tsx` — no `PromoCode` model yet (still marked optional/phase-2 in the spec).
  - Pricing settings: `TAX_RATE` (0.08), `DELIVERY_FEE` (9.99), `FREE_DELIVERY_THRESHOLD` (99) — env-driven in `config/settings.py`, defaults mirror `web/src/lib/checkout.ts` / `web/src/config/store.ts` so recomputed totals match the frontend's checkout preview.
- What is still broken / not started: Stripe checkout intent + webhook, django-otp 2FA, chat `sender_type`. See increments 5-7 in `docs/backend-spec.md`.
- Latest test/build status: `python manage.py test` → **108 passed** (90 in `shop`+`api` combined for the new work, rest pre-existing in `chat`; one expected traceback printed mid-run from a deliberately-mocked OpenAI failure test — not a real failure). `python manage.py check` clean. `makemigrations --check --dry-run` → no changes detected.

## Files in Flight

None — increments 3 and 4 both committed. Next session starts fresh on increment 5 (Stripe).

## Changed This Session

- **Increment 3** (commit `63b835c`): `backend/api/models.py` (+`Profile`), `backend/api/serializers.py` (+`MeSerializer`), `backend/api/views.py` (`MeView` gains `PATCH`), `backend/api/tests.py` (updated `MeViewTests` + new PATCH tests), `backend/shop/models.py` (+`Address`, single-default-per-user logic in `save()`), `backend/shop/admin.py`, `backend/shop/serializers.py` (+`AddressSerializer`), `backend/shop/views.py` (+`AddressViewSet`), `backend/shop/tests.py` (Address model + endpoint tests), `backend/config/urls.py` (registered `addresses` router), migrations `api/0005_profile.py` + `shop/0002_address.py`.
- **Increment 4** (commit `21a750a`): `backend/shop/models.py` (+`Order`, `OrderItem`, `generate_order_number()`), `backend/shop/serializers.py` (+`OrderItemSerializer`, `OrderSerializer`, `OrderCreateSerializer`, `PROMO_CODES`), `backend/shop/views.py` (+`OrderViewSet`), `backend/shop/admin.py` (+`OrderAdmin` with inline `OrderItem` + status actions), `backend/shop/tests.py` (Order model + endpoint tests), `backend/config/settings.py` (+`TAX_RATE`/`DELIVERY_FEE`/`FREE_DELIVERY_THRESHOLD`), `backend/.env.example`, `backend/config/urls.py` (registered `orders` router), migration `shop/0003_order_orderitem.py`.
- Both increments verified live via `manage.py runserver` + `curl` (PATCH `/api/me/`, POST/GET `/api/addresses/`, POST/GET `/api/orders/`) — response shapes and computed totals confirmed correct, then test users cleaned up from the dev DB.

## Failed Attempts

- (Carried from increment 1/2) Tried `ProductImage.image` as a Django `ImageField` — failed `manage.py check` because Pillow isn't installed. Went with `url = URLField` instead since the frontend has no real product images yet. Revisit if real photography is introduced.

## Important Context

- `docs/backend-spec.md` is the source of truth for the full 7-increment plan.
- Frontend's actual `/products` query params (see prior session notes) are already matched exactly by the backend — not the spec prose's `in_stock`/`min_price`/`max_price` variants.
- `Address` model fields (`full_name`, `line1`, `line2`, `city`, `postal_code`, `phone`, `label`, `is_default`) follow the spec's model list verbatim. Note this does **not** match the frontend's `CheckoutAddress` TS interface shape (`firstName`/`lastName` split, no `line2`) used in the not-yet-wired checkout flow (`web/src/lib/checkout.ts`) — that reconciliation is deferred until the frontend actually calls `/api/addresses/` or `/api/orders/`; the Order's `shipping_address` JSON snapshot currently stores the `Address` model's own field names (`full_name`, etc.), not the frontend's `firstName`/`lastName` shape.
- Order line items reference products **by slug** (matches `CartItem.slug` already used client-side and the slug-based `/api/products/{slug}/` lookup convention), not by numeric id.
- `Order.number` is generated via `shop.models.generate_order_number()` (random `DT-######`, retried on collision) at model-instantiation time — not a two-step create-then-update — to avoid a uniqueness race under concurrent order creation.
- Order totals formula (must match `web/src/components/commerce/OrderSummary.tsx` exactly): `discount = subtotal * promo_rate`; `delivery_fee = 0 if pickup else (0 if subtotal >= FREE_DELIVERY_THRESHOLD else DELIVERY_FEE)` (threshold check uses **pre-discount** subtotal, matching the frontend); `tax = TAX_RATE * (subtotal - discount)` (delivery fee is not taxed); `total = subtotal - discount + delivery_fee + tax`.
- `POST /api/orders/` always sets `user=request.user` and `email=request.user.email` — there is no guest-order path through this endpoint yet. `Order.user` is nullable at the model level (`on_delete=SET_NULL`) to leave room for a future guest-checkout/Stripe-intent flow (increment 5) without a schema change.
- `PROMO_CODES` in `shop/serializers.py` is a hardcoded dict (not a DB model) mirroring the frontend's `VALID_PROMOS` placeholder in `PromoCode.tsx`. The spec's `PromoCode` model is explicitly optional/phase-2 — revisit if real promo management via Django admin becomes a requirement.
- `MeSerializer` (`api/serializers.py`) is a plain `serializers.Serializer` (not `ModelSerializer`) spanning both `User` and `Profile` fields; it calls `Profile.objects.get_or_create()` on both read and write so every user transparently gets default `language="en"`/`theme="light"` even if a `Profile` row doesn't exist yet (no signal-based auto-creation — kept explicit/visible in the view instead).
- Do not migrate this backend off Django (explicit lock-in decision, see `AGENTS.md`/spec doc).
- Nothing was pushed to origin this session — commits are local only.

## Next Step

Start increment 5: add the `stripe` dependency; `POST /api/checkout/intent/` (validate stock, compute total server-side via the same logic `OrderCreateSerializer` already uses, create a Stripe PaymentIntent, return `client_secret`); `POST /api/webhooks/stripe/` (CSRF-exempt, verify signature, on `payment_intent.succeeded` mark order paid + decrement stock + notify — note stock is currently decremented at order-creation time in increment 4, so reconcile whether Stripe-flow orders should decrement at intent-creation or at webhook-confirmation instead, to avoid double-decrementing). Add `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` to `.env.example`. See `docs/backend-spec.md` increment 5.

## Commands to Run First

```bash
cd backend
git status --short
git log --oneline -5
./.venv/bin/python manage.py check
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py test
```
