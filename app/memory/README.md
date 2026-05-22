# Graph Memory Engine (SQLite)
> **Persistent ACID-Compliant Knowledge Graph**

Unlike traditional stateless chatbots, AegisDesk remembers users across sessions.

## Core Features
1. **Entity-Relation Extraction**: The LLM extracts triplets (e.g., `user --[HAS_ISSUE]--> VPN`) in the background.
2. **Dynamic Few-Shot Routing**: We store manually taught routing examples in the `routing_examples` table. On startup, these are embedded into a dense vector space to provide autonomous Zero-Token intent routing.
3. **Pruning**: Retention jobs automatically garbage collect stale nodes.
