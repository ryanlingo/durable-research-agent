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
    await session.publish(
        {
            "side": "without",
            "type": "step",
            "run_id": rid,
            "status": session.without.status,
            "tokens": session.without.tokens,
            "message": f"Resuming run_id={rid} from checkpoint…",
        }
    )
    task = asyncio.create_task(run_without_temporal(session, run_id=rid))
    session.tasks["live_without"] = task


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
