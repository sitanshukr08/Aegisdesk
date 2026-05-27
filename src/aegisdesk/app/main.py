import os

os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from fastapi import FastAPI
from contextlib import asynccontextmanager
from aegisdesk.app.rag.pipeline import shutdown_router, async_get_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-warm the semantic router so it doesn't block the event loop on first request
    await async_get_router()
    yield
    await shutdown_router()

from aegisdesk.app.api.auth import router as auth_router
from aegisdesk.app.api.endpoints import router as api_router
from aegisdesk.app.observability.tracing import setup_tracing

app = FastAPI(
    title="HCLTech AI Service Desk Bot",
    version="2.0.0",
    description="Enterprise RAG-powered IT support bot with Streaming & Graph Memory.",
    lifespan=lifespan
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
