# ADR 0003: Agent-First Documentation

> **Verified for AegisDesk v0.1.0 (Phase 16)**


> **Verified for AegisDesk v0.1.0 (Phase 16)**


## Status

Accepted.

## Context

AegisDesk is expected to be worked on by both humans and AI coding agents. Without clear navigation docs, agents load too much context and humans spend review time reconstructing intent from code.

## Decision

Use agent-first documentation:

- a root `AGENTS.md`
- a `docs/context-map.md`
- folder-level README files
- ADRs for architecture decisions
- explicit known limitations

Documentation should be concise, concrete, and honest about current versus planned behavior.

## Consequences

- New contributors can orient quickly.
- Agents can read fewer files per task.
- Architecture decisions are reviewable.
- Docs need to stay updated when boundaries change.
