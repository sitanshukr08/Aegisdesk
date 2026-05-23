# AegisDesk API Server

The `app/api` directory contains the FastAPI routing layer that exposes our LangGraph swarm to external clients (e.g., CLI, Web Dashboards, Slack Bots).

## 🧭 API Versioning

All API endpoints are mounted under a strict `/v1/` prefix (e.g., `/v1/query`, `/v1/health`). This ensures backward compatibility for enterprise clients as we migrate toward `v2` endpoints featuring WebSocket integration.

## 🌊 Server-Sent Events (SSE) Streaming

AegisDesk operates asynchronously. Because agentic operations (like searching logs or querying Active Directory) take 2–15 seconds, we cannot use standard HTTP `POST` responses.

Instead, the `/v1/query` endpoint returns a `StreamingResponse` with `media_type="text/event-stream"`.
The LangGraph `astream` execution yields structured JSON chunks representing:
1. Tool start events (e.g., `{"type": "status", "content": "Running ipconfig..."}`)
2. Final LLM tokens (e.g., `{"type": "token", "content": "The "}`)
3. Interrupt states requiring Human-in-the-Loop approval.

### 🛡️ Information Disclosure Sanitization
Raw API exceptions (such as LLM provider errors, internal stack traces, and Organizational IDs) are caught and natively suppressed before they hit the SSE HTTP response stream. The pipeline securely logs the raw exception trace internally and bubbles up a sanitized, generic error code to the client.

### ⏱️ Async Rate Limit Resilience
To protect the `uvicorn` workers from being blocked by LLM provider rate limits (HTTP 429), the API layer utilizes a custom asynchronous exponential backoff wrapper. 
```python
# LLM invocations are wrapped to avoid blocking the event loop
await asyncio.sleep(2 ** attempt)
```
This ensures transient rate limit errors are handled silently without deadlocking concurrent streams.

## 🔐 Authentication & Rate Limiting

- **JWT Auth**: The FastAPI server relies on OAuth2PasswordBearer. The `auth_service.py` validates JWTs signed by the `JWT_SECRET_KEY` specified in `.env`.
- **RBAC**: Endpoints are scoped. A user with the `"user"` role cannot trigger endpoints protected by `Depends(get_current_admin)`.

### Memory Leak Prevention (`TTLCache`)
We maintain a synchronous proxy to the LangGraph execution using `cachetools.TTLCache`.
This cache tracks active user sessions and automatically evicts dead or stalled connections after 30 minutes, protecting the FastAPI `uvicorn` workers from Out-Of-Memory (OOM) crashes during concurrent load.
