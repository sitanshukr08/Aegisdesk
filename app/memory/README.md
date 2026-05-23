# Memory & Context Architecture

The `app/memory` directory contains the state management and retrieval engines that give AegisDesk long-term contextual awareness across sessions.

## 🧠 Dual-Store Architecture

AegisDesk relies on a heavily decoupled memory architecture:
1. **ChromaDB (Vector Space)**: Used for rapid semantic search over uploaded manuals, standard operating procedures, and historical resolved tickets.
2. **SQLite (Semantic Graph)**: Used for LangGraph checkpointing (`AsyncSqliteSaver`). It provides ACID-compliant, thread-safe state persistence allowing a user to resume a ticket hours after closing their CLI/browser.

### 🛡️ Strict Session Isolation
Memory graphs are explicitly bound to uniquely generated session IDs (`uuid.uuid4().hex[:8]`). This prevents cross-session memory hallucination where an agent erroneously believes it has "already answered" a query based on a previous session's cached SQLite edges. 

*(Note: UUID generation is a demo/testing isolation pattern. In a production deployment, session IDs are strictly derived from the authenticated user's JWT `sub` claim).*

## 🕸️ Waggle-Inspired Graph Traversal

Unlike standard naive RAG (Retrieve-And-Generate), AegisDesk uses a deterministic graph-based retrieval pipeline inspired by Waggle/K-hop traversal models:

1. **Entity Extraction**: The LLM extracts key nouns (e.g., "VPN", "Cisco AnyConnect") from the user's stream.
2. **K-Hop Expansion**: The retriever searches the SQLite metadata graph for tickets linked to those specific entities, expanding outward up to 2 degrees (e.g., `VPN` -> `Gateway Timeout` -> `Firewall Rule #42`).
3. **Temporal Weighting**: Tickets resolved within the last 72 hours are heavily weighted in the graph edges, ensuring the agent retrieves context relevant to ongoing, active outages.

## ⚡ The CrossEncoder Injection Pipeline

Once the vector and graph stores return raw chunks, we do not blindly dump them into the LLM context window (which wastes tokens and confuses the LLM).

1. **Re-ranking**: We pass the chunks through a lightweight CrossEncoder (e.g., PyTorch BGE CrossEncoder).
2. **Thresholding**: Any chunk with a relevance score `< 0.65` is aggressively pruned.
3. **Context Injection**: The surviving, highly-dense chunks are formatted into markdown and injected into the LangGraph state (`state["context"]`), guaranteeing the LLM only hallucinates when explicitly instructed to.
