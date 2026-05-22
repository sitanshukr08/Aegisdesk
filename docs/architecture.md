# Architecture

AegisDesk is an Autonomous IT Agent built on LangGraph. It is designed with a **CLI-first** testing boundary and a **FastAPI** enterprise integration layer.

## The AegisDesk Engine (`src/aegisdesk/core/`)

The core of the system is a LangGraph State Machine.

### The Agent State
```python
class AgentState(TypedDict):
    session_id: str
    user_id: str
    query: str
    messages: Annotated[list, add_messages] # Persistent Conversation History
    intent_category: Optional[str]
    context: Optional[str]
    final_answer: Optional[str]
```

### The Query Flow
1. **Intent Routing**: The `route_intent` node classifies the user query (e.g., 'greeting', 'it_support', 'system_diagnostic').
2. **Retrieval**: The `retrieve_internal` node expands the query, injects Semantic Graph Memory facts, and pulls chunks from ChromaDB.
3. **Reranking**: BGE Cross-Encoder scores the chunks.
4. **Answer Generation & Tool Calling**: The `generate_answer` node invokes the `LLMFactory`. 
   - If the LLM returns a text answer, the graph routes to `end`.
   - If the LLM generates a tool call, the graph routes to the `tools` node.
5. **The ToolNode (Autonomous Execution)**: The graph executes the requested tool (e.g. `ping_network`, `update_jira_ticket`) and routes back to `generate_answer` so the LLM can read the tool output.

## Security & Human-in-the-Loop (HITL)

AegisDesk has powerful OS-level tools. To prevent security incidents, the LangGraph engine is compiled with a security interrupt:
```python
app_graph = workflow.compile(checkpointer=memory, interrupt_before=["tools"])
```
When running locally via the CLI, if the LLM attempts to run a tool, the graph physically pauses execution. The `aegisdesk` CLI intercepts the state and uses `typer.confirm()` to ask the user for approval. If approved, the graph dynamically resumes.

## Persistence Model

SQLite stores durable application state via the `AsyncSqliteSaver`. This includes:
- User chat history and `AgentState` checkpoints
- NetworkX Knowledge Graph Memory edges
- Incident Tickets

ChromaDB purely stores vector embeddings and handles similarity search.

## Delivery Surfaces

1. **CLI (`aegisdesk`)**: The primary local administrative surface. It handles `init`, `ingest`, and `ask` with beautiful `Rich` console outputs.
2. **API (`app/api/endpoints.py`)**: A headless wrapper for enterprise integrations. It streams the LangGraph transitions via Server-Sent Events (SSE). It allows external systems like Slack or Zendesk to invoke AegisDesk over HTTP.
