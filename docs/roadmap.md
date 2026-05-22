# Roadmap

This roadmap tracks the evolution of AegisDesk from a RAG prototype to an Enterprise Autonomous IT Platform.

## Phase 1: Architecture Foundation
Status: **Completed**
- Built foundational docs and `aegisdesk` package scaffolding.

## Phase 2: CLI MVP
Status: **Completed**
- Implemented Typer CLI (`aegisdesk init`, `ingest`, `ask`, `doctor`).

## Phase 3: Persistence Upgrade
Status: **Completed**
- Migrated from JSONL/Pickle to SQLite and `AsyncSqliteSaver`.
- Implemented continuous conversational memory inside LangGraph.

## Phase 4: Provider Abstraction
Status: **Completed**
- Created the `LLMFactory` to seamlessly switch between OpenAI, Groq, and local models.

## Phase 5: Enterprise Hardening
Status: **Completed**
- Introduced rotating JSON-formatted file logging (`src/aegisdesk/observability/logger.py`).
- Silenced console noise and built comprehensive failure-recovery tests.

## Phase 6: Autonomous Diagnostic Tools (HITL)
Status: **Completed**
- Built `src/aegisdesk/core/tools.py` with live Windows diagnostics (`ping`, `ipconfig`).
- Intercepted the LangGraph `ToolNode` with `interrupt_before=["tools"]` to prompt users via the CLI for permission to execute OS commands.

## Phase 7: Rebranding & Enterprise API Parity
Status: **Completed**
- Renamed the project from "DeskBot" to **AegisDesk**.
- Connected `app/api/endpoints.py` to the new LangGraph pipeline.
- Built mock cloud integrations (Jira, Slack, Okta) in `integration_tools.py` to allow AegisDesk to operate headlessly.

---

## Phase 8: Multi-Agent Swarms
Status: **Planned**
- Break the monolithic LangGraph into specialized agents (e.g. `NetworkAgent`, `HRAgent`, `AccessAgent`).
- Implement a Supervisor node to delegate tasks.

## Phase 9: React UI Dashboard
Status: **Planned**
- Build a web interface that consumes the FastAPI endpoints.
- Allow administrators to view chat histories, ticket escalations, and manually approve HITL Tool Interrupts via the UI.
