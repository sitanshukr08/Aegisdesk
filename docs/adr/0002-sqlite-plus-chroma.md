# ADR 0002: SQLite Plus Chroma Persistence

> **Verified for AegisDesk v0.1.6 (Phase 16)**


> **Verified for AegisDesk v0.1.6 (Phase 16)**


## Status

Accepted.

## Context

The prototype stores graph memory in a sqlite-vec file and stores vectors in Chroma. sqlite-vec is not a good long-term persistence layer for user memory, ticket state, document metadata, or collaboration.

The project needs durable state without making local setup heavy.

## Decision

Use SQLite for application state and Chroma for vector search.

SQLite owns:

- users
- sessions
- messages
- documents
- document chunks
- memory edges
- tickets
- runs

Chroma owns:

- embeddings
- vector collections
- similarity search indexes

SQLite stores Chroma IDs so retrieved chunks can be traced back to documents and ingestion runs.

## Consequences

- Local CLI setup stays simple.
- Memory can be queried and migrated without loading sqlite-vec files.
- Ticket and run history becomes auditable.
- A future Postgres migration remains possible if hosted usage requires it.
