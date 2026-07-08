# Goal

Build `devops-target-api` — the Django backend for the DevOps Target computer shop. Serves the storefront and the logged-in app: auth, product catalog, cart/orders, payments, live chat, notifications. Pairs with the `devops-target-web` Next.js frontend.

## Project Shape (read this first)

This is **one half of a two-repo project**:

- `devops-target-api` (this repo) — Django + DRF + Channels. Backend/API only.
- `devops-target-web` — Next.js 16 + TypeScript frontend. Separate repo/folder (`../web`).

Locked stack decision: **Django for the backend** (built-in admin, auth, 2FA fit the feature list), **Next.js for the frontend**. Do not migrate this to FastAPI.

## Current State

- Branch: `main` (clean, up to date with origin).
- Remote: `git@github.com:developmentopstarget/devops-target-api.git` (private).
- Deployed target: Render (ASGI/Daphne for Channels, Postgres, Redis).
- Backend apps (`backend/`):
  - `api/` — models `Item` (generic, placeholder), `Notification` (with mark-read / mark-all-read); `MeView` for current user.
  - `chat/` — `Message` model, `consumers.py`, `routing.py` — working websocket live chat.
  - `config/` — settings, `asgi.py` (Channels), urls.
- Stack in place: DRF + `djoser` (token auth), `channels` + `channels-redis` + `daphne` (websockets), `openai` (AI chat), `psycopg2` (Postgres), `whitenoise`, Dockerfile + docker-compose + entrypoint.
- Dev DB: SQLite (`db.sqlite3`); Postgres is env-switchable and the production target.

## Files in Flight

None. Working tree clean.

## Changed Recently (housekeeping session)

- Repo renamed `react-django-app` → `devops-target-api` on GitHub.
- Local folder moved to `~/AI/Projects/devops-target/api`.
- Remote URL updated to the new name; connection verified.
- Repo set to private.
- Pruned ~60 stale remote-tracking branches.

## Important Context

- Backend of a 2-repo project; frontend lives at `../web` (`devops-target-web`).
- This repo still contains a **legacy Vite/JS frontend** under `frontend/`. It is being **retired** — its working React logic is being ported into `../web` (Next.js). Backend work should target the DRF API + Channels, not this old frontend.
- Current models are generic placeholders (`Item`) — the shop needs real commerce models.
- Auth is token-based via djoser. Live chat auth flows over the websocket (see `CHAT_WEBSOCKET_AUTH_TIMEOUT_SECONDS` in settings).
- CORS/CSRF must allow the Next.js origin.
- Full plan: see `devops-target-roadmap.md` (in the Mockups design project).

## Next Step

Phase 3 — commerce data model: add `Category`, `Product` (specs as JSON), `ProductImage`, `Cart`, `CartItem`, `Order`, `OrderItem`, `Address`; migrations, serializers, viewsets, and Django admin registration (admin = the product/order management UI). Then Phase 4 integrations: 2FA (django-otp), email, Twilio SMS, Stripe payments + webhook.

## Commands to Run First

- `pwd`
- `git branch --show-current`
- `git status`
- `git log --oneline -5`
- `python manage.py check`
- `python manage.py migrate` / `python manage.py test`
