# FastAPI Backend (App)
> **AegisDesk Core Application Server**

This directory contains the primary FastAPI server that exposes AegisDesk's intelligence to external clients (UIs, CLI headless mode, etc.).

## Architecture
- **API**: Modern asynchronous FastAPI utilizing Server-Sent Events (SSE) to stream chunks of reasoning back to the client in real-time.
- **Middleware**: Secured with strict CORS and Rate-Limiting.
- **Tracing**: Fully instrumented with `OpenTelemetry` for Jaeger distributed tracing. Every agent hop is tracked.
