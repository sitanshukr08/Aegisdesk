# `src/aegisdesk/persistence/`

This folder will contain durable storage code.

## Target Storage

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

Chroma owns embeddings and similarity search indexes.

## Boundary Rule

Core services should call repository functions or classes from this package. They should not embed SQL or Chroma collection details directly.

## Migration Notes

The first persistence PR should replace pickle graph memory with SQLite-backed `memory_edges` while preserving the current ability to query a user's known facts.
