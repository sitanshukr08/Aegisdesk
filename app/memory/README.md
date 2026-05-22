# Graph Memory (`app/memory/`)

> **Verified for AegisDesk v0.1.0 (Phase 16)**

**ACID-Compliant Persistent Semantic Graphs**

Legacy systems rely on volatile NetworkX objects. AegisDesk uses `sqlite-vec` to persist memory via local SQLite.
- **`context_assembler.py`**: Evaluates User, Issue, and Hardware subgraph traversals dynamically. Instead of truncating arbitrarily, it slices the top 50 semantic candidates and routes them through a PyTorch CrossEncoder to locate exact graph memory injections without overflowing API token limits.\n