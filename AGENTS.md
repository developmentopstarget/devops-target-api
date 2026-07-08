# AGENTS.md

## Project

React + Django REST app.

This repository is the working codebase for the React-Django-App project. Treat the linked Obsidian project note as long-term project memory, but treat the current repository state as the source of truth for actual code.

## External AI-OS context

Before doing meaningful work, read these Obsidian AI-OS context files:

* `/Users/user/Library/CloudStorage/Dropbox/Obsidian/AI-OS-Vault/_META/Claude-Context/master-context.md`
* `/Users/user/Library/CloudStorage/Dropbox/Obsidian/AI-OS-Vault/_META/Claude-Context/technical-context.md`
* `/Users/user/Library/CloudStorage/Dropbox/Obsidian/AI-OS-Vault/_META/Claude-Context/ai-workflows-context.md`
* `/Users/user/Library/CloudStorage/Dropbox/Obsidian/AI-OS-Vault/01-PROJECTS/Technical/React-Django-App.md`

If a listed Obsidian file does not exist, say which file is missing and continue with the available repo context. Do not invent missing project history.

## External context rules

* Treat the Obsidian project note as long-term project memory.
* Treat this repository as the current working codebase.
* Do not edit Obsidian files unless explicitly asked.
* Before architecture changes, compare the repo state with the Obsidian project note.
* After major completed work, suggest the exact note update that should be added to the Obsidian project file.
* Do not copy large Obsidian content into repo files.
* Do not expose secrets, credentials, private notes, or personal data in commits.

## Stack

* Frontend: React + Tailwind CSS
* Backend: Django + Django REST Framework
* Auth: use existing project auth patterns
* Database: use current project config unless explicitly asked otherwise
* Deployment: inspect existing deployment config before making assumptions

## Working rules

* Inspect the existing code before editing.
* Make minimal, production-safe changes.
* Do not introduce new dependencies unless necessary.
* Preserve existing API contracts unless the task explicitly changes them.
* Prefer small patches over rewrites.
* Do not edit secrets, `.env`, or credential files.
* Do not commit generated/cache files.
* Do not commit `.claude/` unless explicitly requested.
* Do not change architecture unless the task requires it.
* Do not rewrite working code only for style.
* If project state conflicts with Obsidian notes, report the mismatch before changing architecture.

## Backend workflow

Before backend edits, inspect relevant Django files, usually including:

* `backend/manage.py`
* `backend/*/settings.py`
* relevant app models, serializers, views, URLs, consumers, tests
* `backend/requirements.txt` or equivalent dependency file

After backend edits, run:

* `cd backend && python manage.py test`

If the command fails because of environment/setup issues, report the exact error and the likely fix. Do not hide failing tests.

## Frontend workflow

Before frontend edits, inspect:

* `frontend/package.json`
* `frontend/src/`
* current routing/navigation structure
* current Tailwind config and responsive patterns, if present

After frontend edits, run the available lint/build command if present.

Check scripts first:

* `cd frontend && cat package.json`

Prefer, in order:

* `cd frontend && npm run build`

Then run lint/test only if scripts exist:

* `npm run lint`
* `npm test`

Preserve responsive behavior and Tailwind structure.

## Mobile-first UI rules

* Design mobile-first by default.
* Desktop must still work, but mobile layout, spacing, navigation, and usability are primary.
* Keep navigation, forms, cards, buttons, and modals usable on small screens.
* Prefer simple responsive Tailwind utilities over heavy abstractions.
* Avoid visual regressions in existing pages.

## Git workflow

Before changes, check:

* `git status --short`

Before editing, understand the active branch and uncommitted changes.

Do not overwrite user changes.

After changes, summarize:

* files changed
* root cause
* what changed
* tests/checks run
* remaining risk
* suggested Obsidian note update

## Debugging rules

* Fix the smallest confirmed issue first.
* Reproduce or trace the bug before patching when possible.
* If a bug involves frontend/backend interaction, inspect both sides.
* For API issues, check request URL, payload shape, response status, serializer/view behavior, permissions, CORS, and frontend state handling.
* For WebSocket/auth issues, check token handling, headers, cookies, CORS, routing, backend consumer logic, and deployment WebSocket support.
* For deployment issues, inspect environment variables, allowed hosts, CORS, CSRF, build logs, runtime logs, static files, and service settings before patching.
* Do not guess deployment causes without checking config or logs.
* If something cannot be verified locally, say exactly what could not be verified.

## Security rules

* Never expose API keys, passwords, tokens, cookies, or private credentials.
* Do not weaken auth, permissions, CORS, CSRF, or validation to make a bug disappear.
* Prefer secure defaults.
* If a requested change creates a security risk, explain the risk and propose the safer implementation.

## Preferred response style

* Be direct and implementation-focused.
* Show exact commands when needed.
* Avoid long explanations unless requested.
* Prefer complete patches and clear next steps.
* Do not give generic advice when repo-specific inspection is possible.

## Final response format after work

Use this format after making changes:

Changed files:

* ...

Root cause:

* ...

What changed:

* ...

Checks run:

* ...

Remaining risk:

* ...

Suggested Obsidian note update:

* ...

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
