# DevOps Target / Niavaran Computer — Master Roadmap
Option B — **build all features** (no deferral). Canonical roadmap; mirrored in the Obsidian journal `DevOps-Target.md`. Last updated 2026-07-09.

> This is the single source of truth for direction. Per-screen UI specs live in `web/docs/design/mockups/`. Backend model/endpoint detail lives in `api/docs/backend-spec.md`. When something here changes, update this file (both repos) + the Obsidian journal.

## Product

DevOps Target is the rebuild of **niavarancomputer.com** (نیاوران کامپیوتر) — a Tehran computer shop. Two repos: `devops-target-web` (Next.js 16 + TS + Tailwind 4) + `devops-target-api` (Django + DRF + Channels). Bilingual EN + Farsi/RTL (Vazirmatn). Non-technical shop owner must be able to run the whole store from the admin.

## Where we are (2026-07-09)

**MVP loop is live end-to-end:** browse real catalog → cart → checkout → real order + server-side totals + atomic stock decrement → Django admin management → customer order history. Auth (djoser) wired. EN + Farsi/RTL with Vazirmatn. Niavaran logo integrated. Django admin working.
Backend increments 1–5 done, 118 tests passing.
**⚠️ Payments = Stripe, which is a DEV STAND-IN only** (Stripe doesn't operate in Iran) — to be replaced per Phase D.

## Locked decisions

1. **Flexible pricing:** every **product AND service** has `pricing_mode = fixed | on_request`.
   - `fixed` → normal price + online checkout.
   - `on_request` → shows "Request a quote / تماس بگیرید" instead of price → customer submits a quote → admin sets the agreed price → customer gets a pay prompt.
2. **Iran payment methods (production):**
   - **Zarinpal** (online gateway) — instant, automated.
   - **Manual bank transfer** — card-to-card (debit card number, usually instant) or **Sheba/IBAN** (slower, up to ~1 business day) — customer **uploads a receipt screenshot**, admin **verifies** the deposit before the order is marked paid.
   - **Never auto-mark a manual payment paid** — a receipt is a claim, not proof; admin approves every one (this is the fake-receipt guard).
   - **Stripe is dev-only** and will be replaced by the above.
3. **Catalog:** adopt the full **Niavaran nested taxonomy** (Persian) — see "Category taxonomy" below.
4. **Admin friendliness:** the admin is non-technical — Farsi admin UI, friendly theme, image uploads (not URL paste), rich-text descriptions.
5. **Scope = Option B:** build all of the above now, not later.

## Build phases (in order)

### Phase A — Catalog data model & taxonomy (backend)
- `Product`: add `pricing_mode` (`fixed`|`on_request`), make `price` nullable, add `type` (`physical`|`service`), `condition` (`new`|`used`).
- Add **Pillow** + real `ImageField` uploads on `ProductImage` (replace URL-only).
- Replace the 6-category placeholder seed with the **full nested Persian Niavaran taxonomy** (non-core groups may start inactive but are all created).
- Migrations + tests.

### Phase B — Admin friendliness (backend)
- **Farsi admin UI** (Django i18n) so the panel is in Persian.
- **`django-unfold`** admin theme (modern, RTL-capable, mobile-friendly).
- Image-upload widget; **rich-text** product descriptions.
- Clear Persian labels/help text; category drag-ordering; bulk activate/deactivate + mark-on-sale; a **staff** (non-superuser) account with only shop models visible.

### Phase C — Quote system (backend + frontend)
- **Backend:** `Quote`/`QuoteRequest` model (product, customer, qty, contact, message, `status`: new → contacted → quoted → approved → closed); admin **quote inbox**; endpoints. Approving a quote with an agreed price **creates a payable `Order`** (`pending_payment`) + notifies the customer.
- **Frontend:** on `on_request` items, product **card + detail** show "Request a quote / تماس بگیرید" (+ Call / WhatsApp) instead of Add-to-cart; **quote request form**; a **requests/quotes list** in the account with a **Pay now** button when approved; notification when a quote is ready.

### Phase D — Iranian payments (backend + frontend)
- **Backend:** `BankAccount` model (bank, card number, Sheba, holder). Manual `Payment` record with **receipt image** + `verification_status` (pending → approved/rejected, verified_by/at); Order state **`awaiting_verification`**. **Zarinpal** gateway (request → callback/verify → mark paid). Refactor the payment seam so Zarinpal + manual coexist (Stripe removed/relegated to dev).
- **Frontend:** payment-method chooser (**online / card-to-card**); bank-account display with copy buttons; **receipt-screenshot upload** + reference number; **awaiting-verification** state; admin **verify receipt** (approve → paid + notify / reject → re-upload). The approved-quote **Pay now** uses this same flow.

### Phase E — Remaining app features
- **2FA** (django-otp; api increment 6) + wire `/verify-2fa`.
- **Support chat** (api increment 7: chat `sender_type` user/ai/staff) + build the `/support` screen (ports the existing Channels websocket + AI).

### Phase F — Content, polish, launch
- Enrich `seed_catalog` with real descriptions/reviews; add **real product images**.
- **`web` CI** (build + lint) + branch protection (match `api`).
- Fix cosmetic `AuthProvider`/`LoginForm` redirect race.
- Deploy: **Render** (api + Postgres + Redis) + **Vercel** (web); production env/keys/gateway; smoke-test the full purchase + quote + manual-payment flows.

## Category taxonomy (Niavaran, Persian)

Top groups (each with subcategories; nesting is 2 levels, `Category.parent` supports it):
کامپیوتر (PC parts: مانیتور، مادربورد، CPU، RAM، کارت گرافیک، هارد اینترنال/اکسترنال، SSD، درایو نوری، پاور، کیس، فن CPU/کیس، کارت صدا) · لپ‌تاپ (لپ‌تاپ، کیف، آداپتور، فن زیرلپ‌تاپ) · لوازم جانبی موبایل و تبلت (شارژر، کابل، محافظ صفحه، قاب، هندزفری/هدست، پاوربانک، پایه، شارژر فندکی، کابل/مبدل، اسپیکر همراه، ساعت هوشمند) · تجهیزات جانبی کامپیوتر (موس/کیبورد/پد، میکروفن، وب‌کم، اسپیکر، فلش، رم‌ریدر، کارت حافظه، کیف/باکس هارد، هاب USB، بلوتوث، هدفون/هدست) · تجهیزات شبکه (مودم/روتر، اکسس‌پوینت، رنج‌اکستندر، مودم 4G، کارت شبکه، سوئیچ/هاب، کابل شبکه، اسپلیتر، کیستون، سوکت، کابل/سوکت تلفن) · فروش ویژه · خدمات (نصب سیستم‌عامل، آنتی‌ویروس، خدمات نرم‌افزاری موبایل، ساخت ایمیل/اپل‌آیدی، نرم‌افزار تخصصی، ارسال پیامک، سیستم گیمینگ/رندر، طراحی سایت) · ماشین‌های اداری (پرینتر، کارتریج) · تجهیزات کارکرده (موبایل و تبلت) · دوربین مدار بسته · دزدگیر.

Most **خدمات (services)** and some hardware are `on_request` (تماس بگیرید).

## Guardrails / notes for future sessions

- Stripe = dev stand-in only; production payments = Zarinpal + manual transfer/receipt.
- Never auto-approve a manual payment; admin verifies every receipt.
- Keep frontend and backend product/order shapes in sync (the mappers in `web/src/lib/checkout.ts` + params in `web/src/lib/products-filter.ts` mirror the Django serializers).
- Update this file + Obsidian `DevOps-Target.md` whenever direction changes.
