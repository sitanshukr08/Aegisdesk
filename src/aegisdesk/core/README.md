# Core Tools & Execution
> **The Autonomous Toolbelt**

This directory defines every action AegisDesk can take.

## Security Constraints
Every tool is built with a "Zero-Trust" mindset:
1. **RCE Defense (`tools.py`)**: Subprocess execution explicitly enforces `shell=False`. Inputs are scrubbed using regex `[^a-zA-Z0-9.\-_]` to eliminate bash metacharacters.
2. **SSRF Defense (`web_tools.py`)**: Outbound HTTP requests undergo pre-flight DNS checks. Any resolution to `127.0.0.1` or `10.0.0.0/8` is aborted instantly.
