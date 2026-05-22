# Contributing

AegisDesk is moving from prototype to product in small, reviewable phases. Keep changes narrow and make the review surface obvious.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For package-based development after the CLI foundation lands:

```bash
pip install -e ".[dev]"
```

Copy `.env.example` to `.env` and fill only the keys needed for the feature you are testing.

## Branches

Use descriptive branches:

```text
codex-project-architecture-cli-first
feature/cli-init-command
fix/cache-isolation
docs/rag-boundaries
```

## PR Standards

A good PR should:

- solve one clear problem
- keep documentation, behavior, and migration work separated where possible
- include validation steps
- call out known limitations honestly
- avoid claiming features are complete before they are implemented

## Coding Standards

- Keep business logic out of API route handlers and CLI commands.
- Put shared behavior in `src/aegisdesk/core/` once the migration starts.
- Use typed Pydantic models for public request/response shapes.
- Prefer repository classes or functions for persistence instead of direct database access in services.
- Add tests for behavior changes, especially cache keys, persistence, retrieval, and ticket escalation.

## Documentation Standards

- Update the closest folder README when changing a module boundary.
- Add an ADR for decisions that affect architecture, storage, public interfaces, or delivery surfaces.
- Keep docs concrete. Describe what exists today separately from what is planned.

## Validation

For documentation-only changes:

```bash
git status --short
python -m compileall app
```

For runtime changes, add focused tests and run:

```bash
python -m pytest
```
