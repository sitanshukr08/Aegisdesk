# ADR 0001: CLI-First Delivery

## Status

Accepted.

## Context

AegisDesk currently runs as a FastAPI prototype. That is useful for demos and integrations, but it makes local workflows depend on a server before the core behavior is stable.

The project needs a first product surface that is easy to run, easy to test, and useful for both humans and coding agents.

## Decision

AegisDesk will ship a local-first CLI before the UI. The API will become a thin wrapper over shared core services after the CLI path is stable.

The planned CLI commands are:

```bash
aegisdesk init
aegisdesk ingest
aegisdesk ask
aegisdesk memory list
aegisdesk tickets list
aegisdesk doctor
aegisdesk api serve
```

## Consequences

- Core behavior must live outside route handlers.
- CLI commands must be small delivery adapters.
- Tests can target the core directly without starting a web server.
- UI work waits until the CLI and API contracts are clearer.
