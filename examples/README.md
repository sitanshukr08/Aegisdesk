# AegisDesk Examples

This directory contains standalone scripts for validating specific components of the architecture outside of the FastAPI runtime.

## 🧪 Security Validation

To manually trigger the Tier 3 Security guardrails and SSRF testing, run:
```bash
python examples/test_security.py
```
This script will:
1. Attempt an unauthenticated query (should 401).
2. Login and attempt a benign network query.
3. Attempt an SSRF attack (querying `169.254.169.254`), proving that the pipeline intercepts the malicious intent.

## 📚 Document Ingestion

To test the PyPDFLoader and ChromaDB ingestion pipeline:
```bash
python examples/test_features.py
```
This script manually embeds a dummy IT document to verify that `fastembed` and `chromadb` are properly synchronized in your `.venv`.
