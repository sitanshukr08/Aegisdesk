<p align="center">
  <strong>AegisDesk</strong>
</p>
<p align="center">
  <strong>Enterprise Autonomous IT Intelligence. Not just a chatbot wrapper.</strong><br>
  A deterministic, zero-token semantic routing swarm designed for zero-trust enterprise IT.
</p>
<p align="center">
  <em>Most systems use slow, monolithic LLM calls that hallucinate and burn API tokens. AegisDesk uses a persistent SQLite Graph Memory, sub-5ms local embeddings, and isolated sub-agents to resolve IT tickets autonomously.</em>
</p>
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/LangGraph-Swarm-orange.svg" alt="LangGraph">
  <img src="https://img.shields.io/badge/ACID-SQLite-green.svg" alt="SQLite">
</p>

---

### The Problem with RAG in the Enterprise
Your AI forgets context when the window closes, hallucinates network commands, and burns through thousands of tokens just trying to figure out if it should query a database or ping a server. Legacy systems rely on "prompt engineering" a massive, monolithic agent. 

### The AegisDesk Solution
AegisDesk abandons the "monolithic prompt" anti-pattern. Instead, incoming queries are routed through a hyper-optimized deterministic router directly to specialized worker agents.

1. **Zero-Token Semantic Router**: Uses local `FastEmbed` (`BAAI/bge-small-en-v1.5`) to embed and route intents in **< 5 milliseconds** without hitting an LLM.
2. **Multi-Agent Swarm**: 
    - **Network Agent**: Executes OS-level diagnostics (Ping, Port Scans) with strict Regex RCE sanitization.
    - **Cloud Agent**: Interfaces directly with Azure/AWS, Atlassian, and Okta via secured APIs.
    - **Web Intelligence**: Autonomously navigates and scrapes internal wikis. Protected against SSRF via DNS IP resolution filters.
3. **ACID-Compliant Graph Memory**: Tracks entities and relationships persistently in SQLite.

---

### 📊 Enterprise Benchmarks (50-Query Stress Test)
We subjected AegisDesk's core semantic routing engine to a rigorous 50-query IT Helpdesk simulation.

* **Avg Latency**: `4.47 ms` per query (Zero-Bloat ONNX Inferencing)
* **Token Cost**: `$0.00` (100% Local Inference for routing)
* **Direct Match Rate**: `70%` exact sub-agent routing. The remaining 30% dynamically fall back to the secure RAG evaluator, guaranteeing a `100%` resolution pipeline without dropping queries.

---

## 🛠️ Quick Start

### Installation

You can install AegisDesk directly from PyPI:
```bash
pip install aegisdesk
```

#### Developer Installation (From Source)
```bash
git clone https://github.com/sitanshukr08/Aegisdesk.git
cd Aegisdesk
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### Initialization
```bash
# Initialize data structures, logs, and environments
aegisdesk init

# Ingest HR / IT Documentation into the ChromaDB Vector Store
aegisdesk ingest ./docs/vpn_troubleshooting.pdf
```

### CLI Execution
AegisDesk features a beautiful, Rich-powered interactive CLI for headless server deployments.
```bash
aegisdesk ask "Can you ping the corporate gateway and check if my Okta token expired?"
```

---

## 🛡️ Zero-Trust Security Protocols
AegisDesk is hardened against Red Team exploits:
* **RCE Prevention:** `shell=True` is explicitly disabled. All OS inputs are stripped of shell metacharacters (`&`, `|`, `;`, `$`, `<`).
* **SSRF Mitigation:** All web scraper requests undergo pre-flight DNS resolution. Any attempt to scrape private, loopback, or link-local subnets aborts instantly.
* **Denial of Wallet:** The LangGraph Supervisor dynamically counts recursive agent `tool_calls` and explicitly halts infinite loops.

```text
=============================== tests coverage ================================
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
app\rag\graph.py                            120     62    48%
app\rag\pipeline.py                          83     40    52%
src\aegisdesk\core\llm_factory.py            29      4    86%
src\aegisdesk\core\web_tools.py              70     15    79%
-------------------------------------------------------------
TOTAL                                      1218    729    40%
```