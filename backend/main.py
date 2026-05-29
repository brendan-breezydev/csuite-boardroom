"""
C-Suite Boardroom — FastAPI application.
Serves the React frontend as static files and exposes the boardroom SSE API.
"""
import asyncio
import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.boardroom import run_boardroom
from backend.models import BoardroomRequest, BoardroomStartResponse

load_dotenv()

app = FastAPI(title="C-Suite Boardroom", version="1.0.0")

# ---------------------------------------------------------------------------
# CORS (dev: allow Vite dev server; prod: same origin)
# ---------------------------------------------------------------------------
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory session store (sufficient for v1 single-instance deployment)
# ---------------------------------------------------------------------------
_sessions: dict[str, asyncio.Queue] = {}
_results: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.post("/api/boardroom", response_model=BoardroomStartResponse)
async def start_boardroom(req: BoardroomRequest):
    session_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    _sessions[session_id] = queue
    asyncio.create_task(run_boardroom(req.situation, session_id, queue))
    return BoardroomStartResponse(session_id=session_id, status="queued")


@app.get("/api/boardroom/{session_id}/stream")
async def stream_boardroom(session_id: str):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    queue = _sessions[session_id]

    async def event_generator():
        try:
            while True:
                event_str = await asyncio.wait_for(queue.get(), timeout=120.0)
                yield event_str
                import json as _json
                try:
                    parsed = _json.loads(event_str.removeprefix("data: ").strip())
                    if parsed.get("type") in ("done", "error"):
                        _sessions.pop(session_id, None)
                        break
                except Exception:
                    pass
        except asyncio.TimeoutError:
            yield f"data: {{\"type\": \"error\", \"message\": \"Session timed out.\"}}\n\n"
            _sessions.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@app.get("/api/boardroom/{session_id}/result")
async def get_result(session_id: str):
    if session_id in _sessions:
        return {"status": "in_progress"}
    if session_id in _results:
        return _results[session_id]
    raise HTTPException(status_code=404, detail="Session not found.")


# ---------------------------------------------------------------------------
# Static file serving — mount AFTER all API routes
# ---------------------------------------------------------------------------
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        return FileResponse(str(index))
