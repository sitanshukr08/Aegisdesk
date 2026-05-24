# Roadmap

> **Verified for AegisDesk v0.1.6 (Phase 16)**


> **Verified for AegisDesk v0.1.6 (Phase 16)**


This roadmap tracks the evolution of AegisDesk from a RAG prototype to an Enterprise Autonomous IT Platform.

## Phase 1 - 7: Foundation & Hardening
Status: **Completed**
- CLI-first Typer setup, `AsyncSqliteSaver` persistent memory, and LLM provider abstractions.
- Live Windows diagnostic tools (`ping`, `ipconfig`) wrapped in Human-in-the-Loop (`interrupt_before`) LangGraph safety boundaries.
- Mock integrations (Jira, Slack, Okta) built in `integration_tools.py`.

## Phase 8 - 11: Swarm Architecture & RCE Mitigation
Status: **Completed**
- Refactored monolithic LangGraph into specialized intent Domains (`NetworkAgent`, `CloudAgent`, `WebAgent`).
- Implemented rigorous RCE mitigation by strictly enforcing `shell=False`, sanitizing shell metacharacters, and explicitly whitelisting subprocess executables.
- Implemented `MAX_TOOL_RECURSION` loop detection to prevent "Denial of Wallet" attacks.

## Phase 12 - 14: Zero-Token Routing & SSRF Defense
Status: **Completed**
- Implemented a local `sentence-transformers/all-MiniLM-L6-v2` Semantic Router. Intent is classified locally via embeddings without burning API tokens.
- Secured the Web Agent against Time-Of-Check to Time-Of-Use (TOCTOU) Server-Side Request Forgery via a custom `DNSPinnedAdapter` that intercepts the HTTP socket layer.

## Phase 15 - 16: Operational Ergonomics & PyPI Readiness
Status: **Completed**
- Shipped `docker-compose.yml` mapping persistent `~/.aegisdesk` volumes and dropping root capabilities (`cap_drop: ALL`).
- Decoupled state from the current working directory, injected an MIT License, and prepped the CLI for PyPI deployment.
- Proved the execution pipeline via End-to-End (`test_e2e.py`) testing.
- Hardened pipeline with Async Rate Limit Resilience, Information Disclosure boundary sanitization, and Strict UUID session isolation.

---

## Phase 17: Tier 3 Enterprise Scaling
Status: **Completed**
- Refactored pipeline to fully asynchronous LangGraph execution.
- Added `ChromaDB` Semantic Response Caching to bypass LLM limits in near-constant time for redundant queries.
- Implemented an `asyncio.Semaphore(10)` and a Sliding Window Token Bucket rate limiter, achieving 100% success rate at N=30 concurrency on constrained free-tier infrastructure.

---

## Phase 18: React UI Dashboard
Status: **Planned**
- Build a web interface that consumes the FastAPI endpoints.
- Allow administrators to view chat histories, ticket escalations, and manually approve HITL Tool Interrupts via the UI.
