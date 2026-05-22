# Zero-Token Semantic Router & Swarm
> **The Brain of AegisDesk**

This module handles the core routing and agent execution.

## 1. Zero-Token Routing (`pipeline.py`)
Incoming queries are embedded locally using `BAAI/bge-small-en-v1.5` (via `fastembed` ONNX execution). This calculates cosine similarity against our offline vocabulary in **< 5 milliseconds**. If the confidence is `>= 0.55`, it routes to a specific agent directly. Otherwise, it safely falls back to the General agent. No LLM API tokens are burned during routing.

## 2. The LangGraph Swarm (`graph.py`)
- **Network Agent**: Executes restricted ICMP/TCP commands.
- **Cloud Agent**: Interfaces with Okta, Azure, AWS.
- **Web Agent**: Secured against SSRF via DNS parsing.
- **General Agent**: RAG fallback for HR/IT policies.
