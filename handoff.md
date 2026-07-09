# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend (`../web`).

Current focus: implementing the commerce backend per `docs/backend-spec.md`, in the 7-increment build order at the bottom of that file. Increments 1 and 2 are done; increments 3-7 (addresses/profile, orders, Stripe, 2FA, chat sender_type) are not started.

## Current State

- Branch: `main` (local commits ahead of last known origin sync — not pushed this session).
- Working tree: clean except `docs/backend-spec.md` (untracked, pre-existing, not committed — not part of this session's scope).
- What works:
  - `shop` app: `Category`, `Product`, `ProductImage`, `Review` models, migrations applied, Django admin registered (list_display/list_filter/search_fields/date_hierarchy, `ProductImage` inline on `Product`).
  - `seed_catalog` management command — idempotent (`update_or_create`), loads 6 categories + 19 products mirroring `web/src/data/products.ts` + `web/src/data/categories.ts`.
  - Public read API: `GET /api/products/` (filters: `category`, `brand`, `ram`, `storage`, `priceMin`, `priceMax`, `minRating`, `inStock`, `search`; sort: `price_asc`, `price_desc`, `newest`, `rating`, default relevance; page-number pagination, page_size=12) — params match `web/src/lib/products-filter.ts` exactly (camelCase, repeatable `category`/`brand`/`ram`/`storage`). `GET /api/products/{slug}/` (detail, with nested images + sku + description). `GET /api/categories/` + `/{slug}/`. `GET/POST /api/products/{slug}/reviews/` (GET public, POST auth-only via `IsAuthenticatedOrReadOnly`, one review per user per product enforced at DB + view level).
  - All public read endpoints scoped to `is_active=True` and set `permission_classes = [AllowAny]` (global default is `IsAuthenticated`, per-view override).
- What is still broken / not started: addresses, extended `/api/me/` profile prefs, orders/order items, Stripe checkout + webhook, django-otp 2FA, chat `sender_type`. See increments 3-7 in `docs/backend-spec.md`.
- Latest test/build status: `python manage.py test` → **77 passed** (40 in `shop`, 37 pre-existing in `api`/`chat`). `python manage.py check` clean. `makemigrations --check --dry-run` → no changes detected (increment 2 added no new models).

## Files in Flight

None — both increments committed. Next session starts fresh on increment 3 (Address model + extended `/api/me/`).

## Changed This Session

- `backend/shop/` — new app: `models.py`, `admin.py`, `serializers.py`, `views.py`, `pagination.py`, `tests.py`, `migrations/0001_initial.py`, `management/commands/seed_catalog.py`.
- `backend/config/settings.py` — added `shop` to `INSTALLED_APPS`, added `LOW_STOCK_THRESHOLD` setting (env-driven, default 5).
- `backend/config/urls.py` — registered `products` and `categories` routers; imports `shop.views`.
- `backend/.env.example` — added `LOW_STOCK_THRESHOLD=5`.
- Two commits: `75c067f` (increment 1 — models/admin/seed), `0e4b23b` (increment 2 — read endpoints).
- Verified live via `manage.py runserver` + `curl` against `/api/products/` and `/api/categories/` — response shapes look correct (pagination envelope, filters, specs JSON).

## Failed Attempts

- Tried `ProductImage.image` as a Django `ImageField` (per spec's "image/url" wording) — failed `manage.py check` because Pillow isn't installed (`fields.E210`). Decided against adding the Pillow dependency since the frontend currently has **no real product images at all** (confirmed: it renders decorative SVG icon placeholders, no `<img>`/`<Image>` anywhere, no image files in `web/public/`). Went with a single `url = URLField` on `ProductImage` instead. Revisit if/when real product photography is introduced — add Pillow + `ImageField` then, or keep URL-only if images will be hosted externally (CDN/S3).

## Important Context

- `docs/backend-spec.md` is the source of truth for the full 7-increment plan and the copy-paste build prompt. It is untracked in git as of this session (pre-existing, not created by this session) — decide whether to commit it.
- Frontend's actual `/products` query params (confirmed by reading `web/src/lib/products-filter.ts` directly, not just the spec doc's own description of them, which uses slightly different names): `category`, `brand`, `ram`, `storage` (all repeatable), `priceMin`, `priceMax`, `minRating`, `inStock` (`"1"` = true), `sort` (`relevance`|`price_asc`|`price_desc`|`newest`|`rating`), `page` (1-indexed, fixed page size 12, no `page_size` param). The backend implements exactly these names, not the `in_stock`/`min_price`/`max_price` variants mentioned in the spec's prose section (the spec's own copy-paste prompt says "mirror the URL params the frontend already uses" — took that as the authoritative instruction over the earlier prose in the same doc).
- `search` filter is implemented (icontains on name/brand/description) per the spec's explicit ask, even though the current `/products` page doesn't wire a search box to it yet (the site's `SearchBar.tsx` posts to a separate `/search` route not built yet).
- Product's `aggregate_rating`/`review_count` exist as **both** a model property (for admin/shell convenience, one query each) and a queryset annotation (`avg_rating`/`reviews_count`, used by the API to avoid N+1 and to support `minRating` filter + `rating` sort). Keep both in sync if the aggregation logic changes.
- SKUs are auto-generated in `seed_catalog` as `DT-` + slug uppercased/dehyphenated, truncated to ~23 chars total — verified no collisions across the current 19 seed products, but re-check if adding more products with similar-prefixed slugs.
- `LOW_STOCK_THRESHOLD` (env var, default 5) drives `Product.stock_status` ("in-stock"/"low-stock"/"out-of-stock").
- Do not migrate this backend off Django (explicit lock-in decision, see `AGENTS.md`/spec doc).
- Nothing was pushed to origin this session — commits are local only.

## Next Step

Start increment 3: `Address` model + owner-scoped CRUD at `/api/addresses/`, and extend `MeView` (`backend/api/views.py`) to support `PATCH` for `first_name`/`email` plus a new `Profile` model (OneToOne on User) exposing `language`/`theme` prefs via `/api/me/`. See `docs/backend-spec.md` increment 3 for full detail.

## Commands to Run First

```bash
cd backend
git status --short
git log --oneline -5
./.venv/bin/python manage.py check
./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py test
```
