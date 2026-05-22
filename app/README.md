# Core Application (`app/`)
This module contains the primary FastAPI server logic and the LangGraph Multi-Agent execution engine.

**Architecture Details:**
- **main.py**: The ASGI entry point utilizing FastAPI. Protected by CORS, JWT, and `cachetools.TTLCache` to prevent unbounded memory scaling.
- The submodules decouple the API layer from the Semantic Memory and Retrieval-Augmented Generation workflows.\n