# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend (`../web`).

Current focus: Phase D Iranian Payments Backend Core.

## Current State

- Branch: `feature/phase-d-payments`
- Working tree: Modified files (`.gitignore`, `backend/shop/apps.py`, `backend/shop/models.py`) and new migration (`backend/shop/migrations/0008_alter_address_options_alter_category_options_and_more.py`).
- What works:
  - Django Admin modernized with responsive Farsi RTL layout using Tehran time zone.
  - Category, Product, Review, Address, QuoteRequest, and Order models fully Farsi localized for navigation.
  - Shop app label configured as "فروشگاه" in Farsi.
  - `QuoteRequest` system automatically creates orders and notifications.
  - `BankAccount` model tracks active bank transfer details.
  - `Payment` model tracks manual bank transfer receipts, reference numbers, and administrative verification.
  - `Order.status` vocabulary updated to include `awaiting_verification`.
  - `Order.save` prevents transition to `paid` if a manual payment receipt is pending review.
  - Endpoints configured:
    - `GET /api/payments/bank-accounts/` to list active accounts.
    - `POST /api/payments/bank-transfer/` to submit receipt image, reference number, set status to `awaiting_verification`, and create notification.
    - `POST /api/payments/zarinpal/initiate/` and `GET /api/payments/zarinpal/callback/` stubs for gateway simulation.
  - Unfold Admin registers `BankAccount` and `Payment` with inline receipt views and admin verification actions.
  - Entire test suite passes with 132 tests, including new regression tests for bank transfers, validation rules, and Zarinpal callbacks.
- Latest test status: `python manage.py test` → **132 passed**.

## Files in Flight

None. Django admin localization and Phase D Backend Core are complete.

## Changed This Session

- **Farsi Localization of Admin Navigation**:
  - `backend/shop/models.py`: Added Farsi Meta `verbose_name` and `verbose_name_plural` for `Category`, `Product`, `Review`, `Address`, `QuoteRequest`, and `Order`.
  - `backend/shop/apps.py`: Set `verbose_name = "فروشگاه"` in `ShopConfig` to display the app label in Farsi.
  - Applied migrations: `shop.0008_alter_address_options_alter_category_options_and_more`.

## Failed Attempts

- Encountered Pillow image validation error in tests due to dummy image bytes; solved by generating a real minimal 1x1 PNG image using PIL.
- Encountered `InvalidStorageError` when media uploads were triggered; solved by adding the `default` key to the `STORAGES` dictionary in `settings.py`.

## Important Context

- Keep `default` storage configuration in `settings.py`'s `STORAGES` when using customized settings.
- Serves media from the `media/` subdirectory inside `backend/`.

## Next Step

Build Phase D Frontend integrations (bank account listing, receipt upload UI, Zarinpal gateway redirect, and payment status checks).

## Commands to Run First

```bash
cd backend
./.venv/bin/python manage.py check
./.venv/bin/python manage.py test
```
