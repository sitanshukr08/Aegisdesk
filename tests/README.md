# AegisDesk Testing & Security Validation

This directory contains the automated test suites for AegisDesk. Because this system is capable of executing OS-level commands and making network requests on behalf of an LLM, the testing infrastructure heavily prioritizes security boundary validation.

## 🧪 Security Test Matrix (RCE & SSRF)

The `test_exploits.py` file strictly validates our Zero-Trust architecture. We test against the following vectors:

### 1. Remote Code Execution (RCE)
We explicitly test that the `IT_SUPPORT_TOOLS` (e.g., `get_system_info`, `kill_process`) reject shell metacharacters:
- **Command Injection**: Appending `&& calc.exe` or `; rm -rf /` must trigger a `Security Error`.
- **Pipeline Exploitation**: Using `|` to pipe outputs into unauthorized binaries must be caught by our Regex denylist.
- **Critical Process Protection**: Attempting to kill protected OS processes (e.g., `csrss.exe`, `lsass.exe`) must fail immediately.

### 2. Server-Side Request Forgery (SSRF)
The `WEB_SCRAPING_TOOLS` (`safe_fetch`, `scrape_web_page`) are tested against:
- **Loopback & Localhost**: `127.0.0.1`, `::1`, `localhost`, `0.0.0.0`.
- **Private Subnets**: `10.x.x.x`, `192.168.x.x`, `172.16.x.x`.
- **Cloud Metadata APIs**: `169.254.169.254` (AWS/Azure IMDS).
- **DNS Rebinding Attacks**: The test suite mocks a custom `socket.gethostbyname` resolver to simulate an IP flipping from a safe external IP to an internal IP between the pre-flight check and the actual `requests.get` call. Our custom `DNSPinnedAdapter` ensures the attack fails.

### 3. Tool Recursion Escalation
If an agent hits the SSRF barrier and tries to "brute force" a scrape by calling the tool repeatedly, the system enforces a strict `n=5` loop limit. You can see the actual live output of this adversarial test [here](../docs/ssrf_verification.txt), demonstrating the graph killing the looping agent and generating an escalation ticket (`INC-XXXXX`).

## 🎭 Mocking Strategies

Testing an agentic swarm asynchronously requires careful isolation:

1. **LLM Mocking**: In `test_e2e.py` and `test_pipeline.py`, we do not hit real OpenAI/Groq endpoints. We use `unittest.mock.patch` to override `get_llm()` with a deterministic Mock that yields specific LangChain `AIMessage` objects (including mocked `tool_calls`).
2. **ChromaDB Isolation**: We use an ephemeral, in-memory Chroma client for unit tests to prevent cross-test contamination and avoid dropping the real `data/` vector store.

## 🚀 Running the Tests

Locally (this is also run automatically by `.github/workflows/ci.yml`):
```bash
pytest tests/ -v
```
