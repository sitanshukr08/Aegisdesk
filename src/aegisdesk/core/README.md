# AegisDesk Core Domain

The `src/aegisdesk/core` module is the beating heart of the system. It contains the Tool definitions, the LLM Provider factories, and the execution pipeline.

## ☁️ Multi-Cloud Integration Depth

AegisDesk claims multi-cloud capability, and it implements this via explicit tools in `integration_tools.py`:
- **AWS**: Implements `boto3` wrappers for checking EC2 instance statuses, querying S3 bucket ACLs, and verifying IAM role attachments. It strictly requires scoped, read-only `AWS_ACCESS_KEY_ID`s.
- **Azure**: Implements `azure-mgmt-compute` and `azure-identity` (DefaultAzureCredential) integrations for querying VM scale sets and Active Directory (Entra ID) user states.
- **Atlassian**: Integrates with Jira Service Management to transition ticket states natively from the LangGraph pipeline.

## 🛡️ Input Validation Beyond Metacharacters

While shell metacharacter stripping (`;`, `&&`) is our Tier 1 defense, we go further:
- **Type Coercion**: Pydantic strictly coerces and validates every argument passed to every tool. An LLM attempting to pass a string instead of an integer for a port number will fail at the Pydantic boundary, returning a soft error to the LLM.
- **Allowlisting**: Tools like `get_system_info` only accept a rigid Enum of commands (e.g., `"ipconfig"`, `"ping"`, `"tasklist"`). Arbitrary commands are instantly rejected.

## 🚦 Tier 3: Human-In-The-Loop (HITL) Architecture

We separate tools into `SAFE_TOOLS` (e.g., `ping`, `read_file`) and `DANGEROUS_TOOLS` (e.g., `kill_process`, `aws_restart_instance`). 

In `pipeline.py`, the LangGraph compiler is explicitly configured with:
```python
workflow.compile(checkpointer=memory, interrupt_before=["dangerous_tools"])
```
This guarantees mathematical execution suspension. The LLM cannot mutate the cloud or OS state without yielding control back to the FastAPI layer, which subsequently forces a `[y/N]` approval via the Typer CLI or Web UI.

### 🛡️ Denial of Wallet (Loop Cutoff)
To protect against runaway infinite loops (e.g., an LLM repeatedly failing to execute a command), the LangGraph Supervisor tracks recursion depth. The agent is halted at exactly `n=5` recursive tool invocations, and the thread is forcibly escalated to a human IT agent via a generated ticket.
