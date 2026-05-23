# AegisDesk CLI

The `src/aegisdesk/cli` module provides a rich, terminal-first interface for IT operators working in headless server environments.

## 💻 Rich Terminal UI

We use `Typer` for command routing and `Rich` for UI presentation. This provides:
- Live streaming Markdown parsing.
- Dynamic spinning indicators during LLM generation.
- Formatted tables for displaying historical IT tickets.

## 🛡️ The CLI Interrupt Loop

The CLI isn't just a basic prompt. Because AegisDesk utilizes a Human-in-the-Loop architecture, the CLI specifically traps `interrupt` states yielded by the backend:

```python
if chunk["type"] == "interrupt":
    # The pipeline has halted, pending approval
    approval = typer.confirm(f"The agent wants to execute a dangerous action: {action}. Approve?")
```
This loop ensures that the remote terminal operator holds the final key to executing sensitive OS commands.
