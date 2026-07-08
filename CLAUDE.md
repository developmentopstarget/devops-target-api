# CLAUDE.md

Project instructions for Claude Code in this repository.

## Role

Act as a senior full-stack engineer and coding assistant.

## Core Rules

- Read existing files before editing.
- Make small, focused changes.
- Do not rewrite unrelated files.
- Preserve the current project structure unless there is a clear reason to improve it.
- Prefer production-ready, maintainable code.
- Do not hardcode secrets, tokens, API keys, or private values.
- Check git status before and after work.

## Git Workflow

- Work from the repository root.
- Use clear branch names for feature work.
- Use descriptive commit messages.
- Never force push unless explicitly requested.
- Keep commits focused on one logical change.

## Frontend Rules

- Use mobile-first layout decisions.
- Keep UI consistent with existing styling.
- Prefer clean React structure and reusable components.
- Avoid adding dependencies unless necessary.

## Backend Rules

- Keep APIs secure and explicit.
- Validate inputs.
- Avoid leaking sensitive data.
- Run available tests after backend changes.

## Verification

Before saying work is complete:

- Check git status.
- Run available tests, lint, or build commands when they exist.
- Summarize what changed and how to verify it.

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
