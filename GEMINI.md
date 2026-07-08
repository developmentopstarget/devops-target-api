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
