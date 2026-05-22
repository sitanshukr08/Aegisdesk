# Core Tooling (`src/aegisdesk/core/`)
**Military-Grade Security Execution**

- **`tools.py`**: The `subprocess` execution layer. All inbound shell payloads are sterilized via strict Regex whitelisting (`sanitize_input`) to prevent RCE parameter injection vectors (`&`, `|`, `>`).
- **`web_tools.py`**: The headless BeautifulSoup4 scraper. Employs Pre-flight DNS validation (`is_safe_url`) to permanently block Server-Side Request Forgery (SSRF) against internal VPC topologies (10.0.x.x, 169.254.x.x).\n