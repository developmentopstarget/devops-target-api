# GEMINI.md

Project instructions for ChatGPT / Gemini work in this repository.

## Role

Act as a senior full-stack engineer and AI coding assistant.

## Working Rules

- Make production-ready changes.
- Prefer small, focused commits.
- Do not rewrite unrelated files.
- Preserve existing project structure unless improvement is necessary.
- Check current files before editing.
- Run available tests, lint, or build checks after code changes.
- Explain only what changed, why, and how to verify.

## Code Style

- Use clean, maintainable code.
- Prefer TypeScript for React projects.
- Prefer secure backend patterns.
- Avoid hardcoded secrets.
- Keep mobile-first UI behavior in frontend work.

## Git Rules

- Work from the repo root.
- Check status before and after changes.
- Never force push unless explicitly requested.
- Use descriptive commit messages.

## Verification

Before saying work is complete, run git status.

Run project-specific checks when available.

## Project Handoff Rule

Every project must keep a root-level `handoff.md` file.

Before ending a coding session, running `/clear`, switching AI tools, stopping work for the day, opening a PR, merging a PR, debugging a major issue, or changing deployment/config behavior, update `handoff.md`.

The handoff must capture the current project state only. Do not include old unrelated conversation history.

Required sections:

# Goal

What we are trying to build, fix, or ship.

## Current State

Include:
- current branch
- working tree status
- what works
- what is still broken
- latest test/build status if known

## Files in Flight

Files actively edited or likely relevant next.

## Changed This Session

What was touched, created, deleted, refactored, configured, or tested.

## Failed Attempts

What was tried but did not work, including the reason if known.

## Important Context

Decisions, assumptions, constraints, warnings, credentials/account context, deployment notes, or "do not change" items.

## Next Step

The single next action to take first in a fresh session.

## Commands to Run First

Exact commands the next AI/dev session should run before editing.
## Project roadmap & status (Option B — all features)

Canonical roadmap: `ROADMAP.md` (this repo). Also mirrored in the Obsidian journal `DevOps-Target.md`. Per-screen UI specs: `web/docs/design/mockups/`. Backend detail: `api/docs/backend-spec.md`.

**Status (2026-07-09):** MVP loop is LIVE — browse real catalog → cart → checkout → real order + atomic stock decrement → Django admin → customer order history. EN + Farsi/RTL (Vazirmatn). Backend increments 1–5 done (118 tests). **Payments = Stripe, a DEV STAND-IN only (to be replaced — Stripe doesn't operate in Iran).**

**Locked decisions:**
- Every product AND service has `pricing_mode = fixed | on_request`. `on_request` → "Request a quote / تماس بگیرید" → admin sets agreed price → customer pays.
- Iran payments: **Zarinpal** (online) + **manual bank transfer** (card-to-card / Sheba) with **receipt-screenshot upload + admin verification**. Never auto-mark a manual payment paid — admin verifies every receipt. Stripe is dev-only.
- Adopt the full Niavaran nested category taxonomy (Persian). Admin must be non-technical-friendly (Farsi admin UI, django-unfold, image uploads).

**Build phases (in order — see ROADMAP.md for detail):**
- **A · Catalog foundation** (backend): Product `pricing_mode`/nullable price/`type`(physical|service)/`condition`(new|used) + Pillow image uploads; full nested Persian category seed.
- **B · Admin friendliness** (backend): Farsi admin UI, `django-unfold` theme, image-upload widget, rich-text descriptions, staff account.
- **C · Quote system** (both): `Quote` model + admin inbox + endpoints; "Request a quote" branch on card+detail; approved quote → payable Order; account requests list + notify.
- **D · Iranian payments** (both): `BankAccount` model; manual `Payment` + receipt + verification (order `awaiting_verification`); Zarinpal gateway; payment-method chooser + receipt upload + admin verify. Replaces the Stripe seam.
- **E · Remaining** : 2FA (django-otp) + `/verify-2fa`; support chat (chat `sender_type` + `/support`).
- **F · Content, polish, launch**: enrich seed + real product photos; `web` CI + branch protection; fix redirect race; deploy Render(api)+Vercel(web) with prod keys/gateway.
