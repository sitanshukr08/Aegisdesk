# Retrieval & LangGraph Swarm (`app/rag/`)
**Zero-Token Deterministic Swarm Architecture**

AegisDesk's core intelligence engine.
- **`graph.py`**: The StateGraph DAG definition. It establishes boundary interrupts, dynamically enforces the "Denial of Wallet" `tool_calls` loop breaker (`n >= 3`), and transitions execution between specialized IT, Web, and Cloud agents.
- **`pipeline.py`**: Exposes the `execute_rag_pipeline` async generator. Handles `Naive Bayes` and `TF-IDF` intent classification to map requests to agents before engaging the heavy LLM API.\n