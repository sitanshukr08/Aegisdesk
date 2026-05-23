# AegisDesk Core Package

The `src/aegisdesk` directory acts as the installable Python library for this project. 
It cleanly separates the **Domain Logic** (Tools, Prompts, LLMs) from the **Presentation Layer** (FastAPI and CLI).

## Architecture Boundaries

By structuring this as a `src/` layout package:
1. **Import Isolation**: It prevents accidental circular imports between the FastAPI server and the core engine.
2. **Reusability**: You can `pip install aegisdesk` into a completely separate Jupyter Notebook or cron-job and invoke the LangGraph pipeline programmatically, without ever booting the web server.

Navigate to `core/` to see the actual tool definitions and security boundaries.
