"""Scripted crash-recovery showcase for talks and offline demos.

No LLM or Temporal required. Animates both sides so the durability
contrast is visible in a few minutes.
"""

from __future__ import annotations

import asyncio

from ui.events import Session

# Canonical pipeline stages shown in the UI stepper
STAGES = [
    "clarifying",
    "planning",
    "retrieving",
    "searching",
    "writing",
    "evaluating",
    "awaiting_approval",
    "completed",
]

# Token costs per stage (illustrative but consistent)
WITHOUT_COSTS = {
    "clarifying": 420,
    "planning": 610,
    "retrieving": 180,
    "searching": 0,
    "writing": 2400,
    "evaluating": 980,
    "awaiting_approval": 0,
    "completed": 0,
}

WITH_COSTS = {
    "clarifying": 420,
    "planning": 610,
    "retrieving": 180,
    "searching": 0,
    "writing": 2400,
    "evaluating": 980,
    "awaiting_approval": 0,
    "completed": 0,
}


def _tokens(total: int) -> dict[str, int]:
    prompt = int(total * 0.72)
    completion = total - prompt
    return {
        "prompt_tokens": prompt,
        "completion_tokens": completion,
        "total_tokens": total,
    }


async def _sleep(session: Session, seconds: float) -> None:
    # Cooperative cancel points for stop/crash controls
    end = asyncio.get_event_loop().time() + seconds
    while True:
        remaining = end - asyncio.get_event_loop().time()
        if remaining <= 0:
            return
        if session.closed:
            raise asyncio.CancelledError()
        await asyncio.sleep(min(0.1, remaining))


async def run_showcase(
    session: Session,
    *,
    crash_at: str = "writing",
    pace: float = 1.0,
) -> None:
    """Animate a dual-run crash experiment.

    pace: multiply all delays (1.0 = default talk tempo).
    crash_at: stage name where both sides are "killed".
    """
    query = session.query
    without_run = f"local-{session.session_id}"
    with_run = f"research-{session.session_id}"

    await session.publish(
        {
            "side": "system",
            "type": "showcase_started",
            "message": "Showcase mode — scripted crash recovery (no API keys required)",
        }
    )

    async def run_side(
        side: str,
        run_id: str,
        costs: dict[str, int],
        *,
        durable: bool,
    ) -> None:
        total = 0
        completed_before_crash: list[str] = []

        await session.publish(
            {
                "side": side,
                "type": "run_started",
                "run_id": run_id,
                "status": "started",
                "tokens": _tokens(0),
                "message": (
                    f"{'Workflow' if durable else 'Process'} started · {run_id}"
                ),
            }
        )
        await _sleep(session, 0.4 * pace)

        for stage in STAGES:
            if stage == crash_at:
                # Mid-step work begins, then crash
                await session.publish(
                    {
                        "side": side,
                        "type": "step",
                        "run_id": run_id,
                        "status": stage,
                        "tokens": _tokens(total),
                        "message": (
                            "Writing draft report…"
                            if stage == "writing"
                            else f"Working on {stage}…"
                        ),
                    }
                )
                await _sleep(session, 1.1 * pace)

                # Non-durable: LLM may already have billed tokens before checkpoint
                partial_waste = int(costs.get(stage, 0) * 0.55) if not durable else 0
                if partial_waste:
                    total += partial_waste
                    await session.publish(
                        {
                            "side": side,
                            "type": "step",
                            "run_id": run_id,
                            "status": stage,
                            "tokens": _tokens(total),
                            "message": (
                                f"LLM call in flight · ~{partial_waste} tokens already billed "
                                f"(not yet checkpointed)"
                            ),
                        }
                    )
                    await _sleep(session, 0.55 * pace)

                await session.publish(
                    {
                        "side": side,
                        "type": "crashed",
                        "run_id": run_id,
                        "status": "crashed",
                        "tokens": _tokens(total),
                        "message": (
                            "Process killed mid-pipeline; in-flight result lost"
                            if not durable
                            else "Worker killed; Event History retained"
                        ),
                    }
                )
                await _sleep(session, 1.2 * pace)

                if durable:
                    await session.publish(
                        {
                            "side": side,
                            "type": "recovered",
                            "run_id": run_id,
                            "status": stage,
                            "tokens": _tokens(total),
                            "message": (
                                f"Worker restarted; resume unfinished Activity "
                                f"'{stage}'; prior Activities not re-run; "
                                f"tokens still {total}"
                            ),
                        }
                    )
                    await _sleep(session, 0.7 * pace)
                    cost = costs.get(stage, 0)
                    total += cost
                    completed_before_crash.append(stage)
                    await session.publish(
                        {
                            "side": side,
                            "type": "checkpoint",
                            "run_id": run_id,
                            "status": "drafted" if stage == "writing" else stage,
                            "tokens": _tokens(total),
                            "message": (
                                f"Activity completed after resume · +{cost} tokens "
                                f"(result kept in Event History)"
                            ),
                        }
                    )
                else:
                    last_good = completed_before_crash[-1] if completed_before_crash else "started"
                    await session.publish(
                        {
                            "side": side,
                            "type": "recovered",
                            "run_id": run_id,
                            "status": last_good,
                            "tokens": _tokens(total),
                            "message": (
                                f"Partial recovery from SQLite at '{last_good}'. "
                                f"Draft missing · recovery logic re-runs paid work."
                            ),
                        }
                    )
                    await _sleep(session, 0.55 * pace)

                    # Incomplete recovery often re-touches earlier steps
                    replan_cost = costs["planning"]
                    total += replan_cost
                    await session.publish(
                        {
                            "side": side,
                            "type": "step",
                            "run_id": run_id,
                            "status": "planning",
                            "tokens": _tokens(total),
                            "message": (
                                f"Re-planning after crash (recovery edge case) · "
                                f"+{replan_cost} tokens wasted"
                            ),
                        }
                    )
                    await _sleep(session, 0.55 * pace)

                    rewrite_cost = costs.get(stage, 0)
                    total += rewrite_cost
                    await session.publish(
                        {
                            "side": side,
                            "type": "step",
                            "run_id": run_id,
                            "status": stage,
                            "tokens": _tokens(total),
                            "message": (
                                f"Re-running {stage} from scratch · "
                                f"+{rewrite_cost} tokens "
                                f"(prior partial bill also wasted)"
                            ),
                        }
                    )
                    await _sleep(session, 0.85 * pace)
                    await session.publish(
                        {
                            "side": side,
                            "type": "checkpoint",
                            "run_id": run_id,
                            "status": "drafted" if stage == "writing" else stage,
                            "tokens": _tokens(total),
                            "message": f"Checkpointed again at '{stage}'",
                        }
                    )
                    completed_before_crash.append(stage)

                continue

            # Normal stage progression
            await session.publish(
                {
                    "side": side,
                    "type": "step",
                    "run_id": run_id,
                    "status": stage,
                    "tokens": _tokens(total),
                    "message": _stage_message(stage, durable),
                }
            )
            await _sleep(session, _stage_delay(stage) * pace)
            cost = costs.get(stage, 0)
            total += cost
            status_name = {
                "clarifying": "clarified",
                "planning": "planned",
                "retrieving": "retrieved",
                "searching": "searched",
                "writing": "drafted",
                "evaluating": "evaluated",
                "awaiting_approval": "awaiting_approval",
                "completed": "completed",
            }.get(stage, stage)

            if stage == "awaiting_approval":
                await session.publish(
                    {
                        "side": side,
                        "type": "awaiting_approval",
                        "run_id": run_id,
                        "status": "awaiting_approval",
                        "tokens": _tokens(total),
                        "message": (
                            "Waiting for Signal"
                            if durable
                            else "Polling SQLite every 2s for approval row"
                        ),
                    }
                )
                await _sleep(session, 0.7 * pace)
                if session.auto_approve:
                    await session.publish(
                        {
                            "side": side,
                            "type": "step",
                            "run_id": run_id,
                            "status": "awaiting_approval",
                            "tokens": _tokens(total),
                            "message": "Approved",
                        }
                    )
                completed_before_crash.append(status_name)
                continue

            if stage == "completed":
                await session.publish(
                    {
                        "side": side,
                        "type": "completed",
                        "run_id": run_id,
                        "status": "completed",
                        "tokens": _tokens(total),
                        "evaluation": {
                            "faithfulness": 0.91,
                            "relevance": 0.88,
                            "overall": 0.90,
                            "reasoning": "Claims are grounded in retrieved context and answer the query.",
                        },
                        "report": _demo_report(query, durable),
                        "message": f"Completed · {total} total tokens",
                    }
                )
                completed_before_crash.append("completed")
                continue

            if stage == "evaluating":
                await session.publish(
                    {
                        "side": side,
                        "type": "checkpoint",
                        "run_id": run_id,
                        "status": status_name,
                        "tokens": _tokens(total),
                        "evaluation": {
                            "faithfulness": 0.91,
                            "relevance": 0.88,
                            "overall": 0.90,
                            "reasoning": "Claims are grounded in retrieved context and answer the query.",
                        },
                        "message": f"Eval overall=0.90 · +{cost} tokens",
                    }
                )
            else:
                await session.publish(
                    {
                        "side": side,
                        "type": "checkpoint",
                        "run_id": run_id,
                        "status": status_name,
                        "tokens": _tokens(total),
                        "message": (
                            f"{'Activity' if durable else 'Checkpoint'} complete · +{cost} tokens"
                        ),
                    }
                )
            completed_before_crash.append(status_name)

        return total  # type: ignore[return-value]

    # Run both sides concurrently with a slight stagger for readability
    without_task = asyncio.create_task(
        run_side("without", without_run, WITHOUT_COSTS, durable=False)
    )
    await _sleep(session, 0.25 * pace)
    with_task = asyncio.create_task(
        run_side("with", with_run, WITH_COSTS, durable=True)
    )
    session.tasks["showcase_without"] = without_task
    session.tasks["showcase_with"] = with_task

    results = await asyncio.gather(without_task, with_task, return_exceptions=True)
    if any(isinstance(r, asyncio.CancelledError) for r in results):
        await session.publish(
            {
                "side": "system",
                "type": "showcase_stopped",
                "message": "Showcase stopped",
            }
        )
        return

    from ui.comparison import build_comparison

    session.comparison = build_comparison(
        session.without.tokens.get("total_tokens", 0),
        session.with_temporal.tokens.get("total_tokens", 0),
        mode="showcase",
    )
    await session.publish(
        {
            "side": "system",
            "type": "comparison",
            "comparison": session.comparison,
            "message": session.comparison["headline"],
        }
    )


def _stage_message(stage: str, durable: bool) -> str:
    messages = {
        "clarifying": "Deciding whether the query needs clarification…",
        "planning": "Producing 2–3 focused search queries…",
        "retrieving": "Retrieving chunks from the fixed local corpus…",
        "searching": (
            "Concurrent Activities for web search…"
            if durable
            else "asyncio.gather for parallel web search…"
        ),
        "writing": "Writing the markdown research report…",
        "evaluating": "LLM-as-judge: faithfulness + relevance…",
        "awaiting_approval": "Human-in-the-loop approval gate…",
        "completed": "Finishing…",
    }
    return messages.get(stage, stage)


def _stage_delay(stage: str) -> float:
    return {
        "clarifying": 0.7,
        "planning": 0.8,
        "retrieving": 0.55,
        "searching": 1.0,
        "writing": 1.2,
        "evaluating": 0.9,
        "awaiting_approval": 0.5,
        "completed": 0.3,
    }.get(stage, 0.6)


def _demo_report(query: str, durable: bool) -> str:
    path = (
        "Temporal Workflow + Activities"
        if durable
        else "asyncio + SQLite checkpoints"
    )
    return (
        f"## Research report\n\n"
        f"**Query:** {query}\n\n"
        f"Durable Execution helps AI agents survive process crashes by recording "
        f"progress in Event History so the run can resume after a Worker dies. "
        f"In this demo path (`{path}`), intermediate model calls are either "
        f"re-run after failure or reused from completed Activities.\n\n"
        f"### Points\n\n"
        f"1. Completed Activity results should not be re-paid after a worker restart.\n"
        f"2. Human-in-the-loop waits should use a Signal, not a live polling process.\n"
        f"3. Evaluation belongs inside the agent control flow, not only as a side script.\n"
    )
