"""Temporal Workflow for the durable research agent.

Control flow and state live here. All LLM / IO work is delegated to Activities.
Human clarification and approval arrive via Signals.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from with_temporal.activities import (
        clarify_activity,
        evaluate_activity,
        plan_activity,
        retrieve_activity,
        search_activity,
        write_activity,
    )


RETRY = RetryPolicy(maximum_attempts=3)
ACTIVITY_TIMEOUT = timedelta(seconds=120)


@workflow.defn
class ResearchWorkflow:
    def __init__(self) -> None:
        self._clarification_answers: str | None = None
        self._approval: str | None = None  # "approved" | "rejected"
        self._status: str = "started"
        self._query: str = ""
        self._search_plan: list[str] = []
        self._refinements: int = 0
        self._history: list[dict[str, Any]] = []
        self._evaluation: dict[str, Any] = {}
        self._total_tokens: dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

    def _add_tokens(self, raw: dict[str, Any]) -> None:
        t = raw.get("_tokens") or {}
        self._total_tokens["prompt_tokens"] += t.get("prompt_tokens", 0)
        self._total_tokens["completion_tokens"] += t.get("completion_tokens", 0)
        self._total_tokens["total_tokens"] += t.get("total_tokens", 0)

    def _set_status(self, status: str, message: str = "") -> None:
        self._status = status
        self._history.append(
            {
                "status": status,
                "message": message or status,
                "tokens": dict(self._total_tokens),
            }
        )

    @workflow.signal
    def submit_clarification(self, answers: str) -> None:
        self._clarification_answers = answers

    @workflow.signal
    def submit_approval(self, decision: str) -> None:
        self._approval = decision

    @workflow.query
    def status(self) -> dict[str, Any]:
        return {
            "status": self._status,
            "query": self._query,
            "search_plan": self._search_plan,
            "refinements": self._refinements,
            "evaluation": self._evaluation,
            "history": self._history[-40:],
            "total_tokens": self._total_tokens,
            "waiting_for_clarification": self._status == "awaiting_clarification",
            "waiting_for_approval": self._status == "awaiting_approval",
        }

    @workflow.run
    async def run(self, query: str, auto_approve: bool = False, max_refinements: int = 1) -> dict[str, Any]:
        self._query = query
        # 1. Clarify
        self._set_status("clarifying", "Clarifying query…")
        clarify_result = await workflow.execute_activity(
            clarify_activity,
            query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(clarify_result)

        effective_query = query
        if clarify_result.get("needs_clarification"):
            if auto_approve:
                # Match non-Temporal demo path: continue with defaults when unattended.
                self._clarification_answers = "(auto) proceed with reasonable defaults"
                self._set_status(
                    "awaiting_clarification",
                    "Clarification needed; auto-continuing (auto_approve)",
                )
            else:
                self._set_status(
                    "awaiting_clarification",
                    "Waiting for clarification signal",
                )
                # Wait indefinitely for a Signal
                await workflow.wait_condition(lambda: self._clarification_answers is not None)
            effective_query = f"{query}\n\nClarification: {self._clarification_answers}"

        # 2. Plan
        self._set_status("planning", "Planning search queries…")
        plan_result = await workflow.execute_activity(
            plan_activity,
            effective_query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(plan_result)
        search_plan: list[str] = plan_result["plan"]
        self._search_plan = search_plan
        self._set_status("planned", f"Planned {len(search_plan)} search queries")

        # 3. RAG
        self._set_status("retrieving", "Retrieving local corpus (RAG)…")
        retrieve_result = await workflow.execute_activity(
            retrieve_activity,
            effective_query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(retrieve_result)
        chunks = retrieve_result["chunks"]

        # 4. Parallel searches
        self._set_status("searching", f"Running {len(search_plan)} web searches as concurrent activities…")
        search_handles = []
        for q in search_plan:
            handle = workflow.start_activity(
                search_activity,
                q,
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=RETRY,
            )
            search_handles.append(handle)
        search_results = []
        for h in search_handles:
            r = await h
            self._add_tokens(r)
            search_results.append(r)
        self._set_status("searched", f"Completed {len(search_results)} searches")

        # 5. Write → Evaluate → Refine
        report_text = ""
        evaluation: dict[str, Any] = {}
        refinements = 0
        while True:
            self._set_status("writing", "Writing draft report…")
            write_result = await workflow.execute_activity(
                write_activity,
                args=[effective_query, search_results, chunks],
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=RETRY,
            )
            self._add_tokens(write_result)
            report_text = write_result["report"]

            context_texts = [c["content"] for c in chunks]
            context_texts += [s["content"] for s in search_results]

            self._set_status("evaluating", "Evaluating faithfulness + relevance…")
            evaluation = await workflow.execute_activity(
                evaluate_activity,
                args=[effective_query, report_text, context_texts],
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=RETRY,
            )
            self._add_tokens(evaluation)
            self._evaluation = {
                "faithfulness": evaluation.get("faithfulness"),
                "relevance": evaluation.get("relevance"),
                "overall": evaluation.get("overall"),
                "reasoning": evaluation.get("reasoning"),
                "passed": evaluation.get("passed"),
            }

            if evaluation.get("passed") or refinements >= max_refinements:
                break
            refinements += 1
            self._refinements = refinements
            self._set_status("refining", f"Evaluation failed — refining (attempt {refinements})")

        # 6. Human approval
        self._set_status("awaiting_approval", "Waiting for approval signal")
        if auto_approve:
            self._approval = "approved"
        else:
            await workflow.wait_condition(lambda: self._approval is not None)

        if self._approval != "approved":
            self._set_status("rejected", "Report rejected by human reviewer")
            return {
                "status": "rejected",
                "query": effective_query,
                "total_tokens": self._total_tokens,
            }

        self._set_status("completed", f"Completed · {self._total_tokens['total_tokens']} total tokens")
        return {
            "status": "completed",
            "query": effective_query,
            "markdown_report": report_text,
            "short_summary": report_text[:280],
            "evaluation": {
                "faithfulness": evaluation.get("faithfulness"),
                "relevance": evaluation.get("relevance"),
                "overall": evaluation.get("overall"),
                "reasoning": evaluation.get("reasoning"),
            },
            "total_tokens": self._total_tokens,
            "refinements": refinements,
        }
