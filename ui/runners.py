"""Live runners that drive real agents and stream events into a session."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from ui.events import Session


async def run_without_temporal(
    session: Session,
    *,
    run_id: str | None = None,
    auto_approve: bool | None = None,
) -> None:
    from without_temporal.agent import run_research

    rid = run_id or session.without.run_id or str(uuid.uuid4())
    approve = session.auto_approve if auto_approve is None else auto_approve

    async def on_event(payload: dict[str, Any]) -> None:
        event = {"side": "without", **payload}
        await session.publish(event)

    try:
        await run_research(
            session.query,
            run_id=rid,
            auto_approve=approve,
            on_event=on_event,
        )
    except asyncio.CancelledError:
        await session.publish(
            {
                "side": "without",
                "type": "crashed",
                "run_id": rid,
                "status": "crashed",
                "tokens": session.without.tokens,
                "message": "Run cancelled / process crashed mid-flight",
            }
        )
        raise
    except Exception as exc:  # noqa: BLE001 — surface to UI
        await session.publish(
            {
                "side": "without",
                "type": "error",
                "run_id": rid,
                "status": "error",
                "tokens": session.without.tokens,
                "message": f"Error: {exc}",
            }
        )


async def run_with_temporal(
    session: Session,
    *,
    workflow_id: str | None = None,
    auto_approve: bool | None = None,
    host: str = "localhost:7233",
) -> None:
    """Start a Temporal workflow and poll status queries into the event stream."""
    from temporalio.client import Client
    from temporalio.service import RPCError

    from with_temporal.worker import TASK_QUEUE
    from with_temporal.workflows import ResearchWorkflow

    approve = session.auto_approve if auto_approve is None else auto_approve
    wid = workflow_id or session.with_temporal.run_id or f"research-{session.session_id}"

    try:
        client = await Client.connect(host)
    except Exception as exc:  # noqa: BLE001
        await session.publish(
            {
                "side": "with",
                "type": "error",
                "status": "error",
                "message": (
                    f"Cannot connect to Temporal at {host}: {exc}. "
                    "Start `temporal server start-dev` and a worker, or use Showcase mode."
                ),
            }
        )
        return

    await session.publish(
        {
            "side": "with",
            "type": "run_started",
            "run_id": wid,
            "status": "started",
            "tokens": session.with_temporal.tokens,
            "message": f"Starting workflow {wid}",
        }
    )

    try:
        handle = await client.start_workflow(
            ResearchWorkflow.run,
            args=[session.query, approve],
            id=wid,
            task_queue=TASK_QUEUE,
        )
    except RPCError as exc:
        # Already started — attach
        if "already" in str(exc).lower() or "WorkflowExecutionAlreadyStarted" in type(exc).__name__:
            handle = client.get_workflow_handle(wid)
            await session.publish(
                {
                    "side": "with",
                    "type": "recovered",
                    "run_id": wid,
                    "status": "started",
                    "message": f"Attached to existing workflow {wid}",
                }
            )
        else:
            await session.publish(
                {
                    "side": "with",
                    "type": "error",
                    "run_id": wid,
                    "status": "error",
                    "message": f"Failed to start workflow: {exc}",
                }
            )
            return
    except Exception as exc:  # noqa: BLE001
        # temporalio may raise WorkflowAlreadyStartedError
        if "AlreadyStarted" in type(exc).__name__ or "already started" in str(exc).lower():
            handle = client.get_workflow_handle(wid)
            await session.publish(
                {
                    "side": "with",
                    "type": "recovered",
                    "run_id": wid,
                    "status": "started",
                    "message": f"Attached to existing workflow {wid}",
                }
            )
        else:
            await session.publish(
                {
                    "side": "with",
                    "type": "error",
                    "run_id": wid,
                    "status": "error",
                    "message": f"Failed to start workflow: {exc}",
                }
            )
            return

    last_status = ""
    last_history_len = 0
    try:
        while True:
            try:
                st = await handle.query(ResearchWorkflow.status)
            except Exception as exc:  # noqa: BLE001
                await session.publish(
                    {
                        "side": "with",
                        "type": "error",
                        "run_id": wid,
                        "message": f"Status query failed: {exc}",
                    }
                )
                await asyncio.sleep(1.0)
                continue

            status = st.get("status", "unknown")
            tokens = st.get("total_tokens") or session.with_temporal.tokens
            history = st.get("history") or []

            if len(history) > last_history_len:
                for item in history[last_history_len:]:
                    await session.publish(
                        {
                            "side": "with",
                            "type": "checkpoint",
                            "run_id": wid,
                            "status": item.get("status", status),
                            "tokens": item.get("tokens") or tokens,
                            "message": item.get("message") or item.get("status"),
                        }
                    )
                last_history_len = len(history)
            elif status != last_status:
                await session.publish(
                    {
                        "side": "with",
                        "type": "step",
                        "run_id": wid,
                        "status": status,
                        "tokens": tokens,
                        "message": f"Status → {status}",
                    }
                )
            last_status = status

            desc = await handle.describe()
            if desc.status.name in ("COMPLETED", "FAILED", "CANCELED", "TERMINATED", "TIMED_OUT"):
                if desc.status.name == "COMPLETED":
                    result = await handle.result()
                    await session.publish(
                        {
                            "side": "with",
                            "type": "completed",
                            "run_id": wid,
                            "status": "completed",
                            "tokens": result.get("total_tokens") or tokens,
                            "evaluation": result.get("evaluation"),
                            "report": result.get("markdown_report"),
                            "message": (
                                f"Workflow completed · "
                                f"{(result.get('total_tokens') or {}).get('total_tokens', 0)} tokens"
                            ),
                        }
                    )
                else:
                    await session.publish(
                        {
                            "side": "with",
                            "type": "error",
                            "run_id": wid,
                            "status": desc.status.name.lower(),
                            "tokens": tokens,
                            "message": f"Workflow ended: {desc.status.name}",
                        }
                    )
                break

            await asyncio.sleep(0.6)
    except asyncio.CancelledError:
        await session.publish(
            {
                "side": "with",
                "type": "crashed",
                "run_id": wid,
                "status": "crashed",
                "tokens": session.with_temporal.tokens,
                "message": (
                    "UI watcher cancelled. If the Worker was killed, restart it. "
                    "The Workflow Execution continues; completed Activities are not re-run on history replay."
                ),
            }
        )
        raise


async def start_live_session(session: Session, sides: str = "both") -> None:
    """Kick off live side(s). sides: both | without | with."""
    if sides in ("both", "without"):
        task = asyncio.create_task(run_without_temporal(session))
        session.tasks["live_without"] = task
    if sides in ("both", "with"):
        task = asyncio.create_task(run_with_temporal(session))
        session.tasks["live_with"] = task
    if sides == "both":
        session.tasks["live_compare"] = asyncio.create_task(
            _publish_live_comparison_when_done(session)
        )


_TERMINAL_WITHOUT = frozenset({"completed", "error", "rejected"})
_TERMINAL_WITH = frozenset(
    {"completed", "error", "failed", "canceled", "cancelled", "terminated", "timed_out"}
)


async def _publish_live_comparison_when_done(session: Session) -> None:
    """When both live sides finish (after any crash+resume), publish savings.

    Do not publish on the first cancelled non-Temporal task: the user may still
    hit Resume. Poll until both sides are terminal or the session closes.
    """
    from ui.comparison import build_comparison

    # Wait for both original tasks at least once so we don't race start.
    initial = [
        t
        for name, t in list(session.tasks.items())
        if name in ("live_without", "live_with") and t is not None
    ]
    if initial:
        await asyncio.gather(*initial, return_exceptions=True)

    # Crash cancels without early; wait for resume to reach a terminal status
    # (or an error that is not mid-flight crash).
    while not session.closed:
        w_task = session.tasks.get("live_without")
        t_task = session.tasks.get("live_with")
        w_status = session.without.status
        t_status = session.with_temporal.status

        without_busy = bool(w_task and not w_task.done())
        with_busy = bool(t_task and not t_task.done())
        without_crashed = session.without.crashed or w_status == "crashed"

        without_terminal = w_status in _TERMINAL_WITHOUT and not without_busy
        with_terminal = t_status in _TERMINAL_WITH and not with_busy

        if without_crashed or without_busy or with_busy:
            await asyncio.sleep(0.4)
            continue
        if without_terminal and with_terminal:
            break
        # Both tasks idle but not terminal (e.g. only one side started)
        if not without_busy and not with_busy:
            if without_terminal or with_terminal:
                # One side finished; other never started — still publish what we have
                break
            await asyncio.sleep(0.4)
            continue
        await asyncio.sleep(0.4)

    if session.closed:
        return

    w = session.without.tokens.get("total_tokens", 0)
    t = session.with_temporal.tokens.get("total_tokens", 0)
    session.comparison = build_comparison(
        w,
        t,
        mode="live",
        re_executed=session.without.re_executed,
        tokens_at_resume=session.without.tokens_at_resume,
    )
    await session.publish(
        {
            "side": "system",
            "type": "comparison",
            "comparison": session.comparison,
            "message": session.comparison["headline"],
        }
    )


async def crash_without(session: Session) -> None:
    task = session.tasks.get("live_without")
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass
    await session.publish(
        {
            "side": "without",
            "type": "crashed",
            "run_id": session.without.run_id,
            "status": "crashed",
            "tokens": session.without.tokens,
            "message": "Killed process mid-run (task cancelled)",
        }
    )


async def resume_without(session: Session) -> None:
    rid = session.without.run_id
    if not rid:
        await session.publish(
            {
                "side": "without",
                "type": "error",
                "message": "No run_id to resume",
            }
        )
        return
    # Clear crashed flag so comparison waiter treats this as active again.
    session.without.crashed = False
    await session.publish(
        {
            "side": "without",
            "type": "step",
            "run_id": rid,
            "status": session.without.status if session.without.status != "crashed" else "started",
            "tokens": session.without.tokens,
            "message": f"Resuming run_id={rid} from checkpoint…",
        }
    )
    task = asyncio.create_task(run_without_temporal(session, run_id=rid))
    session.tasks["live_without"] = task
    # Ensure a comparison waiter is running (first one may still be looping).
    compare = session.tasks.get("live_compare")
    if compare is None or compare.done():
        session.tasks["live_compare"] = asyncio.create_task(
            _publish_live_comparison_when_done(session)
        )


async def approve_without(session: Session, decision: str = "approved") -> None:
    from without_temporal.state import set_approval

    rid = session.without.run_id
    if not rid:
        return
    set_approval(rid, decision)
    await session.publish(
        {
            "side": "without",
            "type": "step",
            "run_id": rid,
            "status": "awaiting_approval",
            "message": f"Approval set to {decision}",
        }
    )


async def approve_with(session: Session, decision: str = "approved", host: str = "localhost:7233") -> None:
    from temporalio.client import Client

    from with_temporal.workflows import ResearchWorkflow

    wid = session.with_temporal.run_id
    if not wid:
        return
    client = await Client.connect(host)
    handle = client.get_workflow_handle(wid)
    await handle.signal(ResearchWorkflow.submit_approval, decision)
    await session.publish(
        {
            "side": "with",
            "type": "step",
            "run_id": wid,
            "status": "awaiting_approval",
            "message": f"Sent approval signal: {decision}",
        }
    )
