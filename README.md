# AegisDesk

> **Enterprise Autonomous IT Intelligence — Multi-Agent Swarm for the Modern Service Desk**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Swarm-orange.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-SSE%20Streaming-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/ACID-SQLite-brightgreen.svg)](https://www.sqlite.org/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Security](https://img.shields.io/badge/Security-Enterprise%20Grade-red.svg)]()
[![License](https://img.shields.io/badge/License-Proprietary%20%2F%20Portfolio%20Demo-lightgrey.svg)]()
[![CI](https://github.com/sitanshukr08/Aegisdesk/actions/workflows/ci.yml/badge.svg)](https://github.com/sitanshukr08/Aegisdesk/actions)
---

AegisDesk is a **next-generation, multi-agent AI system** purpose-built for Enterprise IT Service Desks. It goes far beyond conventional RAG chatbots by combining a deterministic intent router, an ACID-compliant semantic graph memory, and a hardened security layer — delivering sub-second responses while protecting mission-critical infrastructure from hallucination and abuse.

---

## Table of Contents

- [Why AegisDesk?](#why-aegisdesk)
- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage](#usage)
- [Security Model](#security-model)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [Author](#author)

---

## Why AegisDesk?

Traditional IT helpdesk bots suffer from three fundamental problems:

| Problem | Conventional Approach | AegisDesk Approach |
|---|---|---|
| **Slow responses** | Single monolithic LLM call for every query | Zero-Token Semantic Router + specialist worker agents |
| **Unreliable memory** | Ephemeral context window or in-memory graphs | ACID-compliant SQLite-backed Semantic Graph |
| **Security risk** | Unguarded tool calls & open shell access | Zero-Trust command sanitization + SSRF/RCE mitigations |

AegisDesk is engineered for enterprises where accuracy, auditability, and security are non-negotiable.

---

## Architecture Overview

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│          Zero-Token Semantic Router              │
│   (Deterministic intent routing — no LLM call)  │
└──────────┬───────────────────┬──────────────────┘
           │                   │
   ┌───────▼──────┐   ┌────────▼──────────┐   ┌───────────────────┐
   │   Network    │   │  Cloud/Atlassian   │   │  Web Intelligence │
   │  Ops Agent  │   │   Infra Agent      │   │     Agent         │
   │ (ping, port  │   │ (Azure/AWS/Jira)   │   │ (Internal wikis,  │
   │  scan, proc) │   │                   │   │  HR portals)      │
   └──────┬───────┘   └────────┬──────────┘   └────────┬──────────┘
          │                    │                        │
          └────────────────────▼────────────────────────┘
                               │
               ┌───────────────▼───────────────┐
               │  ACID SQLite Semantic Graph   │
               │  + ChromaDB Vector Store      │
               │  + BGE CrossEncoder Reranker  │
               └───────────────┬───────────────┘
                               │
               ┌───────────────▼───────────────┐
               │    FastAPI SSE Streaming API  │
               │  (JWT Auth + RBAC + TTLCache) │
               └───────────────────────────────┘
```

The LangGraph Supervisor orchestrates all agent activity. Recursive tool calls are capped at `n=5` to prevent runaway loops and protect your API budget — any breach triggers escalation to a human IT agent.

---

## Key Features

### 🤖 Multi-Agent Swarm Architecture
Incoming queries are routed directly to specialized worker agents, eliminating the "monolithic prompt" anti-pattern:
- **Network Operations Agent** — OS-level diagnostics (ping, port scans, process enumeration) with strict regex-based RCE sanitization.
- **Cloud Infrastructure Agent** — Direct integration with Azure, AWS, and Atlassian toolchains via secured REST APIs.
- **Web Intelligence Agent** — Headless scraping of internal wikis and HR portals, protected against SSRF via pre-flight DNS resolution.

### 🧠 ACID-Compliant Semantic Graph Memory
Unlike systems that lose context on reboot, AegisDesk uses a custom **SQLite-backed Semantic Graph** (`sqlite-vec` + `langgraph-checkpoint-sqlite`):
- Entities and relational edges are stored persistently across sessions.
- Context is assembled recursively via Waggle-inspired edge traversal.
- A `BAAI/bge-reranker-base` PyTorch CrossEncoder injects the most hyper-relevant subgraph into the LLM context window without overflow.

### ⚡ Server-Sent Events (SSE) Streaming API
- FastAPI backend with native `text/event-stream` responses for real-time, ChatGPT-like UX.
- JWT Authentication and Role-Based Access Control (RBAC) on all endpoints.
- Global `cachetools.TTLCache` prevents memory leaks from long-running sessions.
- CrossEncoder inference is fully decoupled from the ASGI event loop via `asyncio.to_thread`, guaranteeing zero deadlocks under high concurrent load.

### 🛡️ Zero-Trust Security Protocols
- **RCE Prevention** — `shell=True` is explicitly disabled. All OS inputs are stripped of shell metacharacters (`&`, `|`, `;`, `$`, `<`).
- **SSRF Mitigation** — All web scraper requests undergo pre-flight DNS resolution. Loopback, link-local, or private subnet targets trigger an immediate block.
- **Denial-of-Wallet Protection** — LangGraph Supervisor counts recursive `tool_calls`; infinite loops are caught at `n=5` and escalated to a human.
- **Human-in-the-Loop** — Pipeline uses `interrupt_before=["dangerous_tools"]` so critical OS commands are never executed blindly.

### 💻 Rich CLI Interface
A `typer`-powered, `Rich`-rendered interactive CLI for headless server deployments — no browser required.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.10+ |
| **Agent Orchestration** | LangGraph, LangChain |
| **LLM Providers** | Groq (`langchain-groq`), OpenAI (`langchain-openai`), Google Gemini (`google-generativeai`) |
| **Vector Store** | ChromaDB |
| **Graph Memory** | SQLite + `sqlite-vec`, `langgraph-checkpoint-sqlite` |
| **Reranking** | `sentence-transformers` (`BAAI/bge-reranker-base`) |
| **API Framework** | FastAPI + Uvicorn |
| **Streaming** | Server-Sent Events (SSE) |
| **Auth** | JWT + RBAC |
| **CLI** | Typer + Rich |
| **Document Ingestion** | PyPDF, BeautifulSoup4 |
| **HTTP Client** | HTTPX |
| **Caching** | `cachetools.TTLCache` |
| **Container** | Docker |
| **Linting / Typing** | Ruff, Mypy |
| **Testing** | Pytest, pytest-asyncio |

---

## Project Structure

```
AegisDesk/
├── app/
│   ├── api/                  # FastAPI endpoints (SSE streams, JWT auth, RBAC)
│   ├── memory/               # SQLite Semantic Graph + context assemblers
│   ├── rag/                  # LangGraph pipeline, graph definitions, reranking
│   └── db/                   # ChromaDB vector store (Singleton-managed)
│
├── src/aegisdesk/
│   ├── core/
│   │   ├── tools.py          # Sanitized subprocess tooling
│   │   ├── integration_tools.py  # Cloud & Atlassian integrations
│   │   ├── pipeline.py       # Execution engine (Human-in-the-Loop interrupt)
│   │   └── llm_factory.py    # LLMFactory — unified LLM instantiation
│   ├── cli/
│   │   └── main.py           # Rich-rendered Typer CLI
│   └── observability/
│       └── logger.py         # Structured logger (get_logger())
│
├── docs/
│   ├── architecture.md       # Deep-dive architecture documentation
│   ├── roadmap.md            # Development roadmap
│   ├── context-map.md        # File-to-task mapping for contributors
│   └── adr/                  # Architecture Decision Records (ADRs)
│       └── 0002-sqlite-plus-chroma.md
│
├── tests/                    # Pytest test suite
├── examples/                 # Usage examples
├── Dockerfile                # Container build definition
├── pyproject.toml            # Project metadata, dependencies, tooling config
├── requirements.txt          # Pinned dependency list
├── AGENTS.md                 # AI agent collaboration guide
├── CONTRIBUTING.md           # Contributor guidelines
└── test_security.py          # Standalone security validation suite
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- `git`
- (Optional) Docker

### Installation

```bash
git clone https://github.com/sitanshukr08/Aegisdesk.git
cd Aegisdesk

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install the package in editable mode (includes dev tools)
pip install -e ".[dev]"
```

### Docker (Alternative)

```bash
docker build -t aegisdesk .
docker run --env-file .env -p 8000:8000 aegisdesk
```

---

## Configuration

Copy the environment template and fill in the required keys:

```bash
cp .env.example .env
```

Key variables:

```env
# LLM Provider (choose one or more)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=...

# JWT Secret
JWT_SECRET_KEY=your-secret-key

# Cloud Integrations (optional)
AZURE_SUBSCRIPTION_ID=...
AWS_ACCESS_KEY_ID=...
ATLASSIAN_API_TOKEN=...
```

> Only fill the keys needed for the features you are running. Unused providers can be left blank.

---

## Usage

### Initialize AegisDesk

```bash
# Initialize data structures, logs, and environments
aegisdesk init
```

### Ingest IT Documentation

```bash
# Ingest HR / IT documentation into the ChromaDB vector store
aegisdesk ingest ./docs/vpn_troubleshooting.pdf
aegisdesk ingest ./docs/onboarding_guide.pdf
```

### Ask a Question (CLI)

```bash
aegisdesk ask "Can you ping the corporate gateway and check if my Okta token expired?"
```

### Run the API Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The SSE endpoint will be available at `http://localhost:8000`. Authenticate with a JWT token and stream responses in real time.

### Diagnostics

```bash
aegisdesk doctor
```

---

## Security Model

AegisDesk is hardened against common Red Team attack vectors:

| Threat | Mitigation |
|---|---|
| Remote Code Execution (RCE) | `shell=True` disabled; shell metacharacters stripped from all OS inputs |
| Server-Side Request Forgery (SSRF) | Pre-flight DNS resolution blocks private/loopback/link-local targets |
| Infinite Agent Loops (Denial of Wallet) | LangGraph Supervisor caps recursive `tool_calls` at `n=5`; escalates to human |
| Blind OS Command Execution | `interrupt_before=["dangerous_tools"]` enforces Human-in-the-Loop review |
| Memory Leaks | Global `cachetools.TTLCache` with TTL-based garbage collection |
| Async Deadlocks | CrossEncoder PyTorch inference decoupled via `asyncio.to_thread` |

---

## Development

### Coding Standards

- Keep business logic out of API route handlers and CLI commands; place shared behavior in `src/aegisdesk/core/`.
- Never instantiate `ChatGroq` or `ChatOpenAI` directly — always use `get_llm()` from `src/aegisdesk/core/llm_factory.py`.
- Never use `print()` — use `get_logger()` from `src/aegisdesk/observability/logger.py`.
- Use typed Pydantic models for all public request/response shapes.
- Prefer repository classes for persistence over direct database access in services.

### Branch Naming

```
feature/cli-init-command
fix/cache-isolation
docs/rag-boundaries
refactor/memory-graph-edges
```

### Linting & Type Checking

```bash
ruff check .
mypy src/
```

---

## Testing

```bash
# Run the full test suite
python -m pytest

# Run only security tests
python test_security.py

# Run with verbose output
python -m pytest -v tests/
```

Tests cover cache keys, persistence, retrieval, and ticket escalation logic. All runtime behavior changes must be accompanied by tests.

---

## Contributing

AegisDesk is moving from prototype to product in small, reviewable phases. Contributions should be narrow in scope and reviewable.

Every PR must explain:
1. What changed
2. Why it changed
3. What behavior changed (if any)
4. What was intentionally left out
5. What validation was run via the `aegisdesk` CLI

See [CONTRIBUTING.md](./CONTRIBUTING.md) for full guidelines and see [AGENTS.md](./AGENTS.md) for AI agent collaboration rules.

---

## Roadmap

See [`docs/roadmap.md`](./docs/roadmap.md) for the full roadmap. Current version: **v0.1.0 (Phase 16)**.

Planned improvements include:
- Additional worker agents (HR, Procurement, Identity Management)
- OpenTelemetry-based observability tracing
- Multi-tenant RBAC with department-level scoping
- GitHub Actions CI/CD pipeline
- Formal open-source license

---

## Author

**Sitanshu Kumar**
[GitHub: @sitanshukr08](https://github.com/sitanshukr08)

---

> AegisDesk — *Turning the IT Service Desk from a cost center into an autonomous intelligence layer.*