import os
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from fastapi import FastAPI
from app.api.endpoints import router as api_router
from app.api.auth import router as auth_router
from app.observability.tracing import setup_tracing
app = FastAPI(
    title="HCLTech AI Service Desk Bot",
    version="2.0.0",
    description="Enterprise RAG-powered IT support bot with Streaming & Graph Memory."
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the new Auth router
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])

# Register the API router
app.include_router(api_router, prefix="/api/v1")

# Initialize OpenTelemetry Tracing (if configured)
setup_tracing(app)