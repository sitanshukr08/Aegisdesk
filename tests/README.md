# `tests/`

> **Verified for AegisDesk v0.1.0 (Phase 16)**


This folder will hold unit and integration tests.

## Test Strategy

Start with behavior that can run without network access or API keys:

- preprocessing
- cache key construction
- SQLite repositories
- ticket payload construction
- retrieval interfaces with fake providers
- CLI command smoke tests

## Integration Tests

Use fake LLM, fake vision, fake embeddings, and fake ticket providers before adding tests that require real external services.

The first useful integration flow is:

```text
init local state -> ingest sample KB -> ask known IT question -> receive answer
init local state -> ask unknown question -> receive ticket escalation
```
