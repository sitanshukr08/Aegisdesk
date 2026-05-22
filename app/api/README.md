# API Endpoints
> **Secured Communication Layer**

All external requests traverse through this directory. 

## Endpoints
1. `POST /api/v1/auth/token`: Exchanges OAuth2 password requests for cryptographically signed JWTs.
2. `POST /api/v1/query`: The core reasoning endpoint. Requires a valid JWT. Uses `StreamingResponse` to push LangGraph events.
3. `POST /api/v1/ingest`: Admin-only endpoint for uploading IT policy PDFs and HR documents into the ChromaDB Knowledge Base.
