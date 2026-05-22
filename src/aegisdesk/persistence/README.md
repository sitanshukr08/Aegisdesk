# LangGraph Persistence
> **Async Checkpointing**

Implements custom `BaseCheckpointSaver` adapters for LangGraph. By default, it maps thread states into the SQLite database, ensuring that if the execution is interrupted (e.g. waiting on Human-in-the-Loop approval), it can be resumed flawlessly later.
