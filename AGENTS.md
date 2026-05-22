# Agent Guide

This repository is optimized for focused, low-context collaboration between humans and AI agents. Read this file before changing code or docs.

## Start Here

Use `docs/context-map.md` to choose the minimum files needed for the task. Do not load the entire repository unless the change is cross-cutting.

## Architecture Boundary

AegisDesk uses **LangGraph** for its core intelligence and state tracking.
- The Nodes are defined in `app/rag/pipeline.py` and `app/rag/graph.py`.
- The Tools are defined in `src/aegisdesk/core/tools.py` and `integration_tools.py`.
- The Execution Engine is `src/aegisdesk/core/pipeline.py`.

## Working Rules

- **Use the `aegisdesk` CLI.** The CLI is installed via `pip install -e .`. Use `aegisdesk ask` or `aegisdesk doctor` to test changes. Do not run random python scripts directly.
- **Respect the ToolNode Interrupts.** AegisDesk uses `interrupt_before=["tools"]` for Human-in-the-Loop security. If you alter the pipeline execution in `src/aegisdesk/core/pipeline.py`, ensure the interrupt flow logic remains intact so OS commands are never executed blindly.
- **Use the LLMFactory.** Never instantiate `ChatGroq` or `ChatOpenAI` directly in the core logic. Always use `get_llm()` from `src/aegisdesk/core/llm_factory.py`.
- **Use the Logger.** Do not use `print()`. Use `get_logger()` from `src/aegisdesk/observability/logger.py`.

## Task Routing

- Documentation/Positioning: read `README.md`, `docs/roadmap.md`, and `docs/architecture.md`.
- Tool creation: read `src/aegisdesk/core/tools.py` and `app/rag/graph.py`.
- CLI work: read `src/aegisdesk/cli/main.py`.
- Persistence work: read `docs/adr/0002-sqlite-plus-chroma.md`.
- API work: read `app/api/endpoints.py` and `src/aegisdesk/core/pipeline.py`.

## Review Expectations

Every PR should explain:
- what changed
- why it changed
- what behavior changed, if any
- what was intentionally left out
- what validation was run via the `aegisdesk` CLI
