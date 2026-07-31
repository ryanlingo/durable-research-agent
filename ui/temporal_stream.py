"""Map Temporal Workflow status history → Live UI events."""

from __future__ import annotations

from typing import Any


def history_item_to_event(
    item: dict[str, Any],
    *,
    run_id: str,
    fallback_tokens: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Convert one Workflow status-history entry into a session event.

    History is application-level progress (not raw Temporal Event History),
    enriched so the Live UI can show Activity start/complete, waits, and Signals.
    """
    kind = str(item.get("kind") or "status")
    status = str(item.get("status") or "unknown")
    activity = item.get("activity")
    tokens = item.get("tokens") or fallback_tokens or {}
    delta = int(item.get("token_delta") or 0)
    base_msg = str(item.get("message") or status)

    if kind == "activity_start":
        event_type = "step"
        label = "activity"
        msg = base_msg
        if activity and activity not in base_msg:
            msg = f"Starting Activity: {activity}"
    elif kind == "activity_complete":
        event_type = "activity"
        label = "activity"
        msg = base_msg
        if delta:
            msg = f"{base_msg} · +{delta} tokens"
    elif kind == "wait":
        event_type = (
            "awaiting_approval" if status == "awaiting_approval" else "step"
        )
        label = "wait"
        msg = base_msg
    elif kind == "signal":
        event_type = "signal"
        label = "signal"
        msg = base_msg
    elif kind == "terminal":
        event_type = "step" if status != "completed" else "checkpoint"
        label = "terminal"
        msg = base_msg
    else:
        event_type = "checkpoint"
        label = "status"
        msg = base_msg
        if delta and "token" not in msg.lower():
            msg = f"{base_msg} · +{delta} tokens"

    return {
        "side": "with",
        "type": event_type,
        "run_id": run_id,
        "status": status,
        "tokens": tokens,
        "token_delta": delta,
        "kind": kind,
        "activity": activity,
        "label": label,
        "message": msg,
    }


def execution_status_event(
    *,
    run_id: str,
    execution_status: str,
    tokens: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Surface Temporal Workflow Execution status (RUNNING / COMPLETED / …)."""
    name = execution_status.upper()
    return {
        "side": "with",
        "type": "execution",
        "run_id": run_id,
        "status": name.lower(),
        "tokens": tokens or {},
        "kind": "execution",
        "label": "execution",
        "message": f"Workflow Execution status: {name}",
    }
