# API Endpoints (`app/api/`)

> **Verified for AegisDesk v0.1.0 (Phase 16)**

**Ultra-Fast Server-Sent Events (SSE) Streaming Layer**

This module handles asynchronous web traffic.
- **`endpoints.py`**: Utilizes `StreamingResponse` over `text/event-stream` to push chunked LLM outputs from the LangGraph execution engine to the UI in real-time. Protected against Event Loop Deadlocks by offloading ML inferencing to `asyncio.to_thread`.
- **`auth.py`**: JWT token generation and validation. Enforces strict Role-Based Access Control (RBAC), e.g., locking `/ingest` routes strictly to users with the `admin` flag.\n