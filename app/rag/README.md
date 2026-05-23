# AegisDesk RAG & Agent Swarm

The `app/rag` directory orchestrates the LangGraph StateMachine and defines our multi-agent architecture.

## 🔀 The Zero-Token Semantic Router

Standard LLM routers use a prompt like "If the user asks about network, reply 'network'". This costs tokens and introduces 500ms-1500ms of latency per query.

Instead, AegisDesk uses the `analyze_intent()` pipeline. We embed the incoming user query using the local `BAAI/bge-small-en-v1.5` model via `fastembed` and compute cosine similarity against a static vector space of Intents. 
This routes the query to the correct domain agent in **< 5ms with zero LLM API cost**.

## 🐝 The Worker Agents (Sub-Graphs)

Once routed, the query enters specific specialist agents:
1. **Network Agent**: Armed with OS diagnostics tools.
2. **Cloud Agent**: Armed with Jira, AWS, and Azure API wrappers.
3. **Web Agent**: Armed with Wikipedia, Tavily search, and SSRF-protected scraping tools.
4. **General Agent**: RAG-only fallback with no tools, preventing accidental tool invocation on casual conversation.

### 🛠️ Native JSON Tool Calling
Agent system prompts strictly enforce native LLM tool-calling APIs without conversational wrappers. Early architectures that instructed the LLM to output a conversational preamble explaining the tool call failed; strict open-source models (like Llama-3) often hallucinate stringified JSON directly into the chat stream instead of triggering the native LangChain tool hooks. By stripping preambles, Llama-3 natively invokes tools with 100% reliability.

## ⏸️ Tool Invocation & Interrupts

We use a dual-node pattern in `graph.py`. Tools are split by their danger level. If an agent calls a dangerous tool, LangGraph halts the state machine *before* the `ToolNode` executes, yielding an interrupt state to the API layer for manual authorization.
