"""FastAPI experiment dashboard.

Run:
    python -m ui.app
    # or
    uvicorn ui.app:app --reload --port 8765
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ui.events import store
from ui.runners import (
    approve_with,
    approve_without,
    crash_without,
    resume_without,
    start_live_session,
)
from ui.showcase import STAGES, run_showcase

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Durable Research Agent — Experiment UI",
    version="0.1.0",
    description="Side-by-side visualization of non-durable vs Temporal research agents",
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class StartRequest(BaseModel):
    query: str = Field(
        default="How does durable execution help AI agents survive process crashes?"
    )
    mode: str = Field(default="showcase", pattern="^(showcase|live)$")
    auto_approve: bool = True
    pace: float = Field(default=1.0, ge=0.15, le=3.0)
    crash_at: str = "writing"
    sides: str = Field(default="both", pattern="^(both|without|with)$")


class DecisionRequest(BaseModel):
    decision: str = Field(default="approved", pattern="^(approved|rejected)$")


@app.get("/")
async def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(500, "UI static files missing")
    return FileResponse(index_path)


@app.get("/api/meta")
async def meta() -> dict[str, Any]:
    return {
        "stages": STAGES,
        "modes": ["showcase", "live"],
        "default_query": (
            "How does durable execution help AI agents survive process crashes?"
        ),
    }


@app.post("/api/sessions")
async def create_session(body: StartRequest) -> dict[str, Any]:
    session = store.create(
        query=body.query.strip() or body.query,
        mode=body.mode,
        auto_approve=body.auto_approve,
    )
    await session.publish(
        {
            "side": "system",
            "type": "session_created",
            "message": f"Session {session.session_id} · mode={body.mode}",
        }
    )

    if body.mode == "showcase":
        task = asyncio.create_task(
            run_showcase(session, crash_at=body.crash_at, pace=body.pace)
        )
        session.tasks["showcase"] = task
    else:
        await start_live_session(session, sides=body.sides)

    return session.snapshot()


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return session.snapshot()


@app.get("/api/sessions/{session_id}/events")
async def stream_events(session_id: str) -> StreamingResponse:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    async def gen():
        # Send snapshot first so late joiners catch up
        yield _sse({"type": "snapshot", "snapshot": session.snapshot()})
        while not session.closed:
            try:
                event = await asyncio.wait_for(session.queue.get(), timeout=15.0)
                yield _sse(event)
            except asyncio.TimeoutError:
                yield _sse({"type": "ping", "side": "system"})
            except asyncio.CancelledError:
                break

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/sessions/{session_id}/crash/without")
async def api_crash_without(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.mode != "live":
        raise HTTPException(400, "Crash control is for live mode (showcase self-crashes)")
    await crash_without(session)
    return {"ok": True}


@app.post("/api/sessions/{session_id}/resume/without")
async def api_resume_without(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if session.mode != "live":
        raise HTTPException(400, "Resume control is for live mode")
    await resume_without(session)
    return {"ok": True}


@app.post("/api/sessions/{session_id}/approve/without")
async def api_approve_without(session_id: str, body: DecisionRequest) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    await approve_without(session, body.decision)
    return {"ok": True}


@app.post("/api/sessions/{session_id}/approve/with")
async def api_approve_with(session_id: str, body: DecisionRequest) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    try:
        await approve_with(session, body.decision)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, f"Temporal signal failed: {exc}") from exc
    return {"ok": True}


@app.delete("/api/sessions/{session_id}")
async def api_stop(session_id: str) -> dict[str, Any]:
    session = store.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    store.delete(session_id)
    return {"ok": True}


def _sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, default=str)}\n\n"


def main() -> None:
    import uvicorn

    uvicorn.run("ui.app:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
