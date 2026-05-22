# DeskBot UI

A frontend reimagining of [https://github.com/sitanshukr08/deskbot.git) — an IT-support RAG assistant — built with TanStack Start. Monochrome Nothing-style canvas, Perplexity-style focused ask flow, streaming answers, screenshot vision, and auto-escalated tickets.

The UI ships with a built-in **mock streamer** so it's fully demoable without a backend. Connect the real FastAPI server when you're ready.

## Connecting the FastAPI backend

### 1. Run the DeskBot server

```bash
git clone https://github.com/sitanshukr08/deskbot.git
cd deskbot
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Confirm: `curl http://localhost:8000/health` should return `{"status":"ok"}`.

### 2. Enable CORS

In `app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Point the frontend at it

Two options:

- **Build-time** — create `.env` at the project root:
  ```
  VITE_API_BASE_URL=http://localhost:8000
  ```
  Restart the dev server.

- **Runtime (no rebuild)** — go to `/system`, paste the URL in *API base URL*, click **Test** to verify `/health`, then **Save & reload**. The override is stored in `localStorage` and takes precedence over the build-time value.

### 4. Verify

On `/system` the *Backend* card should show **Online** (green pulsing dot). On `/ask`, a question streams real tokens. Attaching an image routes to `/query_with_image`. Uploading on `/knowledge` hits `/ingest`.

### Deployed backend

For a hosted backend (ngrok, Fly, Render, etc.) use the public HTTPS URL in either of the steps above. Ensure CORS allows the frontend's origin.

## Endpoints consumed

| Method | Path                  | Used by             |
| ------ | --------------------- | ------------------- |
| POST   | `/query`              | `/ask` (text)       |
| POST   | `/query_with_image`   | `/ask` (screenshot) |
| POST   | `/ingest`             | `/knowledge`        |
| GET    | `/health`             | `/system`, header   |

All chat responses are consumed as Server-Sent Events.
