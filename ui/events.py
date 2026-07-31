"""In-memory event bus for the experiment dashboard."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


def _now() -> float:
    return time.time()


@dataclass
class SideState:
    status: str = "idle"
    run_id: str | None = None
    tokens: dict[str, int] = field(
        default_factory=lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }
    )
    crashed: bool = False
    report: str | None = None
    evaluation: dict[str, Any] | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Session:
    session_id: str
    query: str
    mode: str  # "showcase" | "live"
    auto_approve: bool = True
    created_at: float = field(default_factory=_now)
    without: SideState = field(default_factory=SideState)
    with_temporal: SideState = field(default_factory=SideState)
    comparison: dict[str, Any] = field(default_factory=dict)
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    tasks: dict[str, asyncio.Task] = field(default_factory=dict)
    closed: bool = False

    async def publish(self, event: dict[str, Any]) -> None:
        if self.closed:
            return
        payload = {
            "ts": _now(),
            "session_id": self.session_id,
            **event,
        }
        side = event.get("side")
        if side == "without":
            self._apply_side(self.without, payload)
        elif side in ("with", "with_temporal", "temporal"):
            payload["side"] = "with"
            self._apply_side(self.with_temporal, payload)
        await self.queue.put(payload)

    def _apply_side(self, side: SideState, event: dict[str, Any]) -> None:
        side.events.append(event)
        if len(side.events) > 200:
            side.events = side.events[-200:]
        if event.get("run_id"):
            side.run_id = event["run_id"]
        if event.get("status"):
            side.status = event["status"]
        elif event.get("type") in ("step", "checkpoint") and event.get("status"):
            side.status = event["status"]
        if event.get("tokens"):
            side.tokens = dict(event["tokens"])
        if event.get("type") == "crashed":
            side.crashed = True
            side.status = "crashed"
        if event.get("type") in ("recovered", "run_started") and side.crashed:
            side.crashed = False
        if event.get("type") == "completed":
            side.status = "completed"
            side.report = event.get("report")
            side.evaluation = event.get("evaluation")
            side.crashed = False
        if event.get("report") and not side.report:
            side.report = event["report"]
        if event.get("evaluation"):
            side.evaluation = event["evaluation"]

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "query": self.query,
            "mode": self.mode,
            "auto_approve": self.auto_approve,
            "without": {
                "status": self.without.status,
                "run_id": self.without.run_id,
                "tokens": self.without.tokens,
                "crashed": self.without.crashed,
                "report": self.without.report,
                "evaluation": self.without.evaluation,
                "events": self.without.events[-80:],
            },
            "with": {
                "status": self.with_temporal.status,
                "run_id": self.with_temporal.run_id,
                "tokens": self.with_temporal.tokens,
                "crashed": self.with_temporal.crashed,
                "report": self.with_temporal.report,
                "evaluation": self.with_temporal.evaluation,
                "events": self.with_temporal.events[-80:],
            },
            "comparison": self.comparison,
        }


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}

    def create(
        self,
        query: str,
        mode: str = "showcase",
        auto_approve: bool = True,
    ) -> Session:
        session_id = uuid.uuid4().hex[:12]
        session = Session(
            session_id=session_id,
            query=query,
            mode=mode,
            auto_approve=auto_approve,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        session.closed = True
        for task in session.tasks.values():
            task.cancel()


store = SessionStore()
