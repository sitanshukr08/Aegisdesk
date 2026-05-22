# Retrieval & LangGraph Swarm (`app/rag/`)

> **Verified for AegisDesk v0.1.0 (Phase 16)**

**Zero-Token Deterministic Swarm Architecture**

AegisDesk's core intelligence engine.
- **`graph.py`**: The StateGraph DAG definition. It establishes boundary interrupts, dynamically enforces the "Denial of Wallet" `tool_calls` loop breaker (`n >= 3`), and transitions execution between specialized IT, Web, and Cloud agents.
- **`pipeline.py`**: Exposes the `execute_rag_pipeline` async generator. Handles `Naive Bayes` and `MiniLM Semantic Embedding` intent classification to map requests to agents before engaging the heavy LLM API.\n