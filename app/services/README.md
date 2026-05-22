# External Services (`app/services/`)
**Isolated 3rd-Party Integrations**

- **`vision_service.py`**: Integrates with specialized VLM (Vision-Language Models) to ingest screenshots of user errors (e.g., BSOD) and extract diagnostic string parameters.
- **`auth_service.py`**: Manages PBKDF2 hashed password comparisons, active session tracking, and JWT asymmetric cryptographic token minting.\n