"""
Non-Temporal research agent.

Realistic "typical production" shape:
- asyncio + tenacity retries
- SQLite checkpoints after every major step
- Human approval via polling a database row
- Manual recovery logic that is incomplete on purpose
"""

from __future__ import annotations

import asyncio
import inspect
import json
import sys
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import (
    AgentState,
    ClarificationRequest,
    ResearchReport,
    SearchResult,
    TokenUsage,
    evaluate_report,
    llm_call,
    retrieve,
    web_search,
)
from without_temporal.state import get_approval, load_state, save_state, set_approval

EventCallback = Callable[[dict[str, Any]], Awaitable[None] | None]


def _log(msg: str) -> None:
    print(f"[without-temporal] {msg}", flush=True)


async def _emit(on_event: EventCallback | None, payload: dict[str, Any]) -> None:
    if not on_event:
        return
    result = on_event(payload)
    if inspect.isawaitable(result):
        await result


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _clarify(query: str) -> tuple[ClarificationRequest | None, TokenUsage]:
    system = (
        "You decide whether a research query needs clarification. "
        "If the query is already specific, return {\"needs_clarification\": false}. "
        "If not, return {\"needs_clarification\": true, \"questions\": [..], \"reason\": \"..\"}."
    )
    text, usage = await asyncio.to_thread(
        llm_call, system, query, None, 0.0
    )
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, usage
    if not data.get("needs_clarification"):
        return None, usage
    return (
        ClarificationRequest(
            questions=data.get("questions", ["Can you be more specific?"]),
            reason=data.get("reason", ""),
        ),
        usage,
    )


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _plan(query: str) -> tuple[list[str], TokenUsage]:
    system = (
        "Produce 2 or 3 focused web search queries for the given research topic. "
        "Return ONLY a JSON list of strings."
    )
    text, usage = await asyncio.to_thread(llm_call, system, query)
    try:
        plan = json.loads(text)
        if isinstance(plan, list):
            return [str(q) for q in plan[:3]], usage
    except json.JSONDecodeError:
        pass
    return [query, f"{query} recent developments"], usage


async def _search_one(q: str) -> SearchResult:
    return await asyncio.to_thread(web_search, q)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _write_report(
    query: str, search_results: list, chunks: list
) -> tuple[str, TokenUsage]:
    context_parts = []
    for c in chunks:
        context_parts.append(f"[{c.title}] {c.content}")
    for s in search_results:
        context_parts.append(f"[web:{s.query}] {s.content}")
    context = "\n\n".join(context_parts)
    system = (
        "You are a research writer. Produce a clear markdown report that answers the query "
        "using only the provided context. Start with a one-paragraph summary."
    )
    user = f"Query: {query}\n\nContext:\n{context}"
    text, usage = await asyncio.to_thread(llm_call, system, user)
    return text, usage


async def run_research(
    query: str,
    run_id: str | None = None,
    auto_approve: bool = False,
    max_refinements: int = 1,
    on_event: EventCallback | None = None,
) -> ResearchReport:
    run_id = run_id or str(uuid.uuid4())
    _log(f"run_id={run_id}")
    await _emit(
        on_event,
        {
            "side": "without",
            "type": "run_started",
            "run_id": run_id,
            "query": query,
            "message": f"Run started ({run_id[:8]}…)",
        },
    )

    # Track paid work that runs again after a checkpoint resume (not merely
    # first-time stages that continue after recovery).
    is_recovery = False
    tokens_at_resume = 0
    draft_present_at_resume = False
    had_evaluation_at_resume = False
    re_executed: list[dict[str, Any]] = []

    async def note_rerun(step: str, usage: TokenUsage, reason: str) -> None:
        """Record a stage that re-paid tokens after partial recovery."""
        entry = {
            "step": step,
            "tokens": int(usage.total_tokens or 0),
            "reason": reason,
        }
        re_executed.append(entry)
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "re_executed",
                "run_id": run_id,
                "status": step,
                "tokens": state.total_tokens.to_dict(),
                "re_executed_step": entry,
                "re_executed": list(re_executed),
                "message": (
                    f"Re-ran {step} after resume · +{entry['tokens']} tokens "
                    f"({reason})"
                ),
            },
        )

    # Attempt recovery from checkpoint
    raw = load_state(run_id)
    if raw:
        is_recovery = True
        _log("Found existing checkpoint — attempting partial recovery")
        state = AgentState(query=raw.get("query", query))
        state.status = raw.get("status", "started")
        state.clarified_query = raw.get("clarified_query")
        state.search_plan = raw.get("search_plan", [])
        # Reconstruct nested objects. This boilerplate is the kind of work
        # every non-durable agent accumulates for crash recovery.
        from shared.types import EvaluationResult, RetrievedChunk, SearchResult

        state.search_results = [
            SearchResult(
                query=r.get("query", ""),
                content=r.get("content", ""),
                source=r.get("source", "web"),
            )
            for r in raw.get("search_results", [])
        ]
        state.retrieved_chunks = [
            RetrievedChunk(**c) for c in raw.get("retrieved_chunks", [])
        ]
        state.draft_report = raw.get("draft_report")
        if raw.get("evaluation"):
            ev = raw["evaluation"]
            eval_tokens = ev.get("tokens") or {}
            state.evaluation = EvaluationResult(
                faithfulness=ev.get("faithfulness", 0),
                relevance=ev.get("relevance", 0),
                overall=ev.get("overall", 0),
                reasoning=ev.get("reasoning", ""),
                tokens=TokenUsage(**eval_tokens) if eval_tokens else TokenUsage(),
            )
        state.approval_status = raw.get("approval_status", "pending")
        tok = raw.get("total_tokens", {})
        state.total_tokens = TokenUsage(**tok) if tok else TokenUsage()
        state.history = raw.get("history", [])
        tokens_at_resume = state.total_tokens.total_tokens
        draft_present_at_resume = bool(state.draft_report)
        had_evaluation_at_resume = bool(state.evaluation)
        # Prior re-ran steps from earlier resume attempts (cumulative waste).
        prior_re = raw.get("re_executed") or []
        if isinstance(prior_re, list):
            re_executed.extend(prior_re)
        _log(
            f"Recovered status={state.status}, plan={len(state.search_plan)} queries, "
            f"tokens_at_resume={tokens_at_resume}"
        )
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "recovered",
                "run_id": run_id,
                "status": state.status,
                "tokens": state.total_tokens.to_dict(),
                "tokens_at_resume": tokens_at_resume,
                "draft_present": draft_present_at_resume,
                "message": (
                    f"Partial recovery from checkpoint at '{state.status}' "
                    f"(tokens so far: {tokens_at_resume}; "
                    f"draft {'present' if draft_present_at_resume else 'missing'})"
                ),
            },
        )
    else:
        state = AgentState(query=query)

    async def checkpoint(step: str, message: str | None = None) -> None:
        state.history.append({"step": step, "ts": time.time()})
        state.status = step
        payload = state.checkpoint()
        # Persist re-ran ledger so a second resume still shows cumulative waste.
        payload["re_executed"] = list(re_executed)
        payload["tokens_at_resume"] = tokens_at_resume
        save_state(run_id, payload)
        _log(f"checkpointed at '{step}' (tokens so far: {state.total_tokens.total_tokens})")
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "checkpoint",
                "run_id": run_id,
                "status": step,
                "tokens": state.total_tokens.to_dict(),
                "re_executed": list(re_executed),
                "message": message
                or f"Checkpointed at '{step}' · {state.total_tokens.total_tokens} tokens",
            },
        )

    # 1. Clarify
    if state.status in ("started",):
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "clarifying",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": "Clarifying query…",
            },
        )
        clarification, usage = await _clarify(query)
        state.total_tokens.add(usage)
        if clarification:
            state.clarification = clarification
            await checkpoint("awaiting_clarification")
            _log("Needs clarification: " + "; ".join(clarification.questions))
            # In a real system the caller would supply answers; for demo we auto-continue
            state.clarified_query = query + " (clarified with defaults)"
        else:
            state.clarified_query = query
        await checkpoint("clarified")

    effective_query = state.clarified_query or query

    # 2. Plan
    if state.status in ("clarified", "started"):
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "planning",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": "Planning search queries…",
            },
        )
        plan, usage = await _plan(effective_query)
        state.search_plan = plan
        state.total_tokens.add(usage)
        await checkpoint("planned", f"Planned {len(plan)} search queries")

    # 3. RAG + parallel search
    if state.status in ("planned", "clarified", "started"):
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "retrieving",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": "Retrieving local corpus (RAG)…",
            },
        )
        chunks, rag_usage = await asyncio.to_thread(retrieve, effective_query, 4)
        state.retrieved_chunks = chunks
        state.total_tokens.add(rag_usage)

        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "searching",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": f"Running {len(state.search_plan)} web searches in parallel…",
            },
        )
        search_coros = [_search_one(q) for q in state.search_plan]
        results = await asyncio.gather(*search_coros)
        state.search_results = list(results)
        # Intentionally do not add search token usage into total here in a
        # durable way if process dies mid-gather — intermediate gather results
        # only land after all complete (partial recovery pain point).
        await checkpoint("searched", f"Searched {len(results)} queries")

    # 4. Write + evaluate + refine
    # Incomplete recovery (intentional): even if evaluation was checkpointed,
    # we re-enter the write/eval loop when draft is missing or status is still
    # mid-pipeline — and we re-evaluate when draft exists without short-circuiting
    # on a saved evaluation. That re-pays judge tokens after some crashes.
    refinements = 0
    while True:
        if state.draft_report is None or refinements > 0:
            rewriting_after_crash = (
                is_recovery and refinements == 0 and not draft_present_at_resume
            )
            await _emit(
                on_event,
                {
                    "side": "without",
                    "type": "step",
                    "status": "writing",
                    "run_id": run_id,
                    "tokens": state.total_tokens.to_dict(),
                    "message": (
                        "Re-writing draft report (draft missing after crash)…"
                        if rewriting_after_crash
                        else "Writing draft report…"
                    ),
                },
            )
            draft, usage = await _write_report(
                effective_query, state.search_results, state.retrieved_chunks
            )
            state.draft_report = draft
            state.total_tokens.add(usage)
            if rewriting_after_crash:
                await note_rerun(
                    "writing",
                    usage,
                    "draft missing after crash (in-flight write was not checkpointed)",
                )
            await checkpoint("drafted")

        reevaluating = is_recovery and had_evaluation_at_resume and refinements == 0
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "evaluating",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": (
                    "Re-evaluating after resume (recovery does not short-circuit "
                    "on saved evaluation)…"
                    if reevaluating
                    else "Evaluating faithfulness + relevance…"
                ),
            },
        )
        context_texts = [c.content for c in state.retrieved_chunks]
        context_texts += [s.content for s in state.search_results]
        evaluation = await asyncio.to_thread(
            evaluate_report, effective_query, state.draft_report or "", context_texts
        )
        state.evaluation = evaluation
        state.total_tokens.add(evaluation.tokens)
        if reevaluating:
            await note_rerun(
                "evaluating",
                evaluation.tokens,
                "judge re-run after resume (incomplete recovery path)",
            )
        await checkpoint(
            "evaluated",
            f"Eval overall={evaluation.overall:.2f} "
            f"(faithfulness={evaluation.faithfulness:.2f}, "
            f"relevance={evaluation.relevance:.2f})",
        )

        if evaluation.passed or refinements >= max_refinements:
            break
        _log(
            f"Evaluation failed (overall={evaluation.overall:.2f}). "
            f"Reason: {evaluation.reasoning}. Refining..."
        )
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "step",
                "status": "refining",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": f"Evaluation failed — refining (attempt {refinements + 1})",
            },
        )
        refinements += 1
        state.draft_report = None  # force rewrite

    # 5. Human approval (polling)
    if state.status != "completed":
        if state.approval_status == "pending":
            set_approval(run_id, "pending")
            await checkpoint("awaiting_approval", "Waiting for human approval (polling SQLite…)")
        if auto_approve:
            set_approval(run_id, "approved")
            state.approval_status = "approved"
            _log("auto-approved")
            await _emit(
                on_event,
                {
                    "side": "without",
                    "type": "step",
                    "status": "awaiting_approval",
                    "run_id": run_id,
                    "tokens": state.total_tokens.to_dict(),
                    "message": "Auto-approved",
                },
            )
        else:
            _log(
                f"Waiting for human approval. "
                f"Run: python -m without_temporal.approve {run_id} approved"
            )
            await _emit(
                on_event,
                {
                    "side": "without",
                    "type": "awaiting_approval",
                    "run_id": run_id,
                    "tokens": state.total_tokens.to_dict(),
                    "message": "Awaiting human approval (poll every 2s)",
                },
            )
            while True:
                status = get_approval(run_id)
                if status in ("approved", "rejected"):
                    state.approval_status = status
                    break
                await asyncio.sleep(2)

    if state.approval_status == "rejected":
        await _emit(
            on_event,
            {
                "side": "without",
                "type": "rejected",
                "run_id": run_id,
                "tokens": state.total_tokens.to_dict(),
                "message": "Report rejected by human reviewer",
            },
        )
        raise RuntimeError("Report rejected by human reviewer")

    re_tokens = sum(int(x.get("tokens", 0) or 0) for x in re_executed)
    report = ResearchReport(
        query=effective_query,
        short_summary=(state.draft_report or "")[:280],
        markdown_report=state.draft_report or "",
        evaluation=state.evaluation,
        total_tokens=state.total_tokens,
        steps=[h["step"] for h in state.history],
    )
    state.final_report = report
    await checkpoint("completed", "Run completed")
    completed_msg = f"Completed · {state.total_tokens.total_tokens} total tokens"
    if re_executed:
        completed_msg += f" · re-ran {len(re_executed)} step(s) (+{re_tokens} tokens after resume)"
    await _emit(
        on_event,
        {
            "side": "without",
            "type": "completed",
            "run_id": run_id,
            "status": "completed",
            "tokens": state.total_tokens.to_dict(),
            "tokens_at_resume": tokens_at_resume if is_recovery else None,
            "re_executed": list(re_executed),
            "re_executed_tokens": re_tokens,
            "evaluation": {
                "faithfulness": report.evaluation.faithfulness if report.evaluation else None,
                "relevance": report.evaluation.relevance if report.evaluation else None,
                "overall": report.evaluation.overall if report.evaluation else None,
                "reasoning": report.evaluation.reasoning if report.evaluation else None,
            },
            "report": report.markdown_report,
            "message": completed_msg,
        },
    )
    return report
