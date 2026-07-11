# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend (`../web`).

Current focus: Phase D Iranian Payments Backend Core.

## Current State

- Branch: `feature/phase-d-payments`
- Working tree: Modified files (`backend/requirements.txt`, `backend/config/settings.py`, `backend/config/urls.py`, `backend/shop/admin.py`, `backend/shop/models.py`, `backend/shop/serializers.py`, `backend/shop/views.py`, `backend/shop/tests.py`) and new migrations.
- What works:
  - Django Admin modernized with responsive Farsi RTL layout using Tehran time zone.
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

None. Phase D Backend Core is complete.

## Changed This Session

- **Phase D Iranian Payments Backend Core**:
  - `backend/shop/models.py`: Created `BankAccount` and `Payment` models. Updated `ORDER_STATUS_CHOICES` to include `awaiting_verification` and hardened `Order.save` to validate state transitions.
  - `backend/config/settings.py`: Configured `MEDIA_URL`, `MEDIA_ROOT`, and updated `STORAGES` to include the `default` backend config.
  - `backend/config/urls.py`: Mounted the bank transfer and Zarinpal views, and served media files in debug mode.
  - `backend/shop/serializers.py`: Added `BankAccountSerializer`, `PaymentSerializer`, and `BankTransferSubmitSerializer` with validation checks.
  - `backend/shop/views.py`: Added view classes `BankAccountListView`, `SubmitBankTransferView`, `ZarinpalInitiateView`, and `ZarinpalCallbackView`.
  - `backend/shop/admin.py`: Registered new models, defined `PaymentInline` for orders, and implemented `approve_payments` and `reject_payments` actions. Hardened `mark_paid` action to trigger save-level validation.
  - `backend/shop/tests.py`: Added `IranianPaymentTests` class with 7 integration and regression tests.
  - Applied migrations `shop.0007_bankaccount_alter_order_status_payment`.

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
