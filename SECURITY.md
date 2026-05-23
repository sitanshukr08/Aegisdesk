# Security Policy

AegisDesk is built from the ground up for Enterprise Zero-Trust environments. This document outlines our security posture, threat mitigation strategies, and roadmap for future security improvements.

## 🛡️ Current Threat Mitigations

### 1. Remote Code Execution (RCE) Prevention
* **Execution Boundary**: `subprocess.run` is explicitly configured with `shell=False`.
* **Metacharacter Stripping**: All user input routed to the Network Ops Agent undergoes strict sanitization, stripping all shell control characters (`&`, `|`, `;`, `$`, `<`).

### 2. Server-Side Request Forgery (SSRF) Protection
* **Pre-flight DNS Resolution**: The Web Intelligence agent executes a pre-flight DNS lookup against all scraping targets.
* **IP Filtering**: If the target resolves to a private subnet (e.g., `10.x.x.x`), loopback (`127.0.0.1`), link-local, or `0.0.0.0`, the request is blocked before the HTTP client is initialized.

### 3. Denial of Wallet & Infinite Loops
* **Recursion Capping**: The LangGraph Supervisor explicitly counts the number of recursive `tool_calls` in a single session.
* **Hard Interrupt**: If the agent attempts `n > 3` loops without producing an answer, the execution is halted and the ticket is escalated to a human.

### 4. Blind Execution Prevention (Human-in-the-Loop)
* **Destructive Tools**: Tools like `kill_process` and `start_process` are classified as Dangerous.
* **LangGraph Interrupt**: The pipeline is compiled with `interrupt_before=["dangerous_tools"]`, physically halting execution and pushing an authorization prompt to the user CLI before mutating the host operating system.

## 🗺️ Security Roadmap

While AegisDesk is heavily fortified, the following enterprise features are planned for upcoming releases:

1. **Secrets Scanning**: Integrate `trufflehog` or `gitleaks` into the CI/CD pipeline to prevent API keys from leaking in commits or agent output.
2. **Comprehensive Audit Logging**: Forward all `get_logger()` events to a centralized SIEM (Splunk/Datadog) for forensic analysis.
3. **Per-User Rate Limiting**: Implement a Redis-backed rate limiter on the FastAPI `/query` endpoint to throttle abusive or runaway queries.
4. **Token-Level Access Scoping**: Transition from basic RBAC to granular OAuth2 scopes (e.g., `agent:read`, `agent:execute_network`, `agent:execute_cloud`).

## Reporting a Vulnerability

If you discover a vulnerability in AegisDesk, please **do not** open a public issue.

Email the maintainer at [sitanshukumar65@gmail.com] with the subject `[SECURITY VULNERABILITY]`. We commit to a 48-hour initial response time and will coordinate a patch before public disclosure.
