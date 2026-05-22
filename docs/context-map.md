# Context Map

> **Verified for AegisDesk v0.1.0 (Phase 16)**


> **Verified for AegisDesk v0.1.0 (Phase 16)**


Use this map to load the smallest useful context for a task.

## Product Or README Changes
Read:
- `README.md`
- `docs/roadmap.md`
- `docs/ARCHITECTURE.md`
- `AGENTS.md`

## CLI Work
Read:
- `src/aegisdesk/README.md`
- `src/aegisdesk/cli/README.md`
- `src/aegisdesk/cli/main.py`
- `docs/adr/0001-cli-first.md`

## Core Agent & Tool Work
Read:
- `src/aegisdesk/core/README.md`
- `src/aegisdesk/core/pipeline.py` (The main LangGraph executor)
- `src/aegisdesk/core/tools.py` (OS-level Tools)
- `src/aegisdesk/core/integration_tools.py` (Cloud API Tools)
- `src/aegisdesk/core/llm_factory.py`

## LangGraph Node Work
Read:
- `app/rag/graph.py (LangGraph Swarm) (LangGraph Swarm)` (The StateGraph definition)
- `app/rag/pipeline.py` (The logic inside the nodes)

## API Work
Read:
- `app/api/README.md`
- `app/main.py`
- `app/api/endpoints.py` (FastAPI SSE Streaming endpoints)
- `app/services/auth_service.py`

## Memory Work
Read:
- `app/memory/README.md`
- `app/memory/graph_store.py`
- `app/memory/extractor.py`
- `docs/adr/0002-sqlite-plus-chroma.md`
