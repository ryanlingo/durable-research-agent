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
        self._last_activity: str | None = None
        self._history_token_cursor: int = 0
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

    def _set_status(
        self,
        status: str,
        message: str = "",
        *,
        kind: str = "status",
        activity: str | None = None,
    ) -> None:
        """Record a progress event for Live UI Queries.

        kind: activity_start | activity_complete | wait | signal | status | terminal
        """
        self._status = status
        if activity:
            self._last_activity = activity
        tokens = dict(self._total_tokens)
        total = int(tokens.get("total_tokens", 0) or 0)
        delta = max(0, total - self._history_token_cursor)
        self._history_token_cursor = total
        self._history.append(
            {
                "status": status,
                "message": message or status,
                "tokens": tokens,
                "token_delta": delta,
                "kind": kind,
                "activity": activity,
                "seq": len(self._history),
            }
        )

    @workflow.signal
    def submit_clarification(self, answers: str) -> None:
        self._clarification_answers = answers
        self._set_status(
            self._status,
            "Received clarification Signal",
            kind="signal",
            activity="submit_clarification",
        )

    @workflow.signal
    def submit_approval(self, decision: str) -> None:
        self._approval = decision
        self._set_status(
            self._status if self._status != "awaiting_approval" else "awaiting_approval",
            f"Received approval Signal: {decision}",
            kind="signal",
            activity="submit_approval",
        )

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
            "last_activity": self._last_activity,
            "waiting_for_clarification": self._status == "awaiting_clarification",
            "waiting_for_approval": self._status == "awaiting_approval",
        }

    @workflow.run
    async def run(self, query: str, auto_approve: bool = False, max_refinements: int = 1) -> dict[str, Any]:
        self._query = query
        self._set_status(
            "started",
            "Workflow Execution started",
            kind="status",
        )

        # 1. Clarify
        self._set_status(
            "clarifying",
            "Starting Activity: clarify_activity",
            kind="activity_start",
            activity="clarify_activity",
        )
        clarify_result = await workflow.execute_activity(
            clarify_activity,
            query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(clarify_result)
        self._set_status(
            "clarifying",
            "Activity completed: clarify_activity",
            kind="activity_complete",
            activity="clarify_activity",
        )

        effective_query = query
        if clarify_result.get("needs_clarification"):
            if auto_approve:
                # Match non-Temporal demo path: continue with defaults when unattended.
                self._clarification_answers = "(auto) proceed with reasonable defaults"
                self._set_status(
                    "awaiting_clarification",
                    "Clarification needed; auto-continuing (auto_approve)",
                    kind="signal",
                )
            else:
                self._set_status(
                    "awaiting_clarification",
                    "Waiting for clarification Signal (Worker can exit)",
                    kind="wait",
                )
                # Wait indefinitely for a Signal
                await workflow.wait_condition(lambda: self._clarification_answers is not None)
            effective_query = f"{query}\n\nClarification: {self._clarification_answers}"

        # 2. Plan
        self._set_status(
            "planning",
            "Starting Activity: plan_activity",
            kind="activity_start",
            activity="plan_activity",
        )
        plan_result = await workflow.execute_activity(
            plan_activity,
            effective_query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(plan_result)
        search_plan: list[str] = plan_result["plan"]
        self._search_plan = search_plan
        self._set_status(
            "planned",
            f"Activity completed: plan_activity · {len(search_plan)} queries",
            kind="activity_complete",
            activity="plan_activity",
        )

        # 3. RAG
        self._set_status(
            "retrieving",
            "Starting Activity: retrieve_activity",
            kind="activity_start",
            activity="retrieve_activity",
        )
        retrieve_result = await workflow.execute_activity(
            retrieve_activity,
            effective_query,
            start_to_close_timeout=ACTIVITY_TIMEOUT,
            retry_policy=RETRY,
        )
        self._add_tokens(retrieve_result)
        chunks = retrieve_result["chunks"]
        self._set_status(
            "retrieved",
            f"Activity completed: retrieve_activity · {len(chunks)} chunks",
            kind="activity_complete",
            activity="retrieve_activity",
        )

        # 4. Parallel searches
        self._set_status(
            "searching",
            f"Starting {len(search_plan)} concurrent search_activity Activities",
            kind="activity_start",
            activity="search_activity",
        )
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
        self._set_status(
            "searched",
            f"Completed {len(search_results)} concurrent search Activities",
            kind="activity_complete",
            activity="search_activity",
        )

        # 5. Write → Evaluate → Refine
        report_text = ""
        evaluation: dict[str, Any] = {}
        refinements = 0
        while True:
            self._set_status(
                "writing",
                "Starting Activity: write_activity",
                kind="activity_start",
                activity="write_activity",
            )
            write_result = await workflow.execute_activity(
                write_activity,
                args=[effective_query, search_results, chunks],
                start_to_close_timeout=ACTIVITY_TIMEOUT,
                retry_policy=RETRY,
            )
            self._add_tokens(write_result)
            report_text = write_result["report"]
            self._set_status(
                "drafted",
                "Activity completed: write_activity",
                kind="activity_complete",
                activity="write_activity",
            )

            context_texts = [c["content"] for c in chunks]
            context_texts += [s["content"] for s in search_results]

            self._set_status(
                "evaluating",
                "Starting Activity: evaluate_activity",
                kind="activity_start",
                activity="evaluate_activity",
            )
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
            self._set_status(
                "evaluated",
                (
                    f"Activity completed: evaluate_activity · "
                    f"overall={evaluation.get('overall')}"
                ),
                kind="activity_complete",
                activity="evaluate_activity",
            )

            if evaluation.get("passed") or refinements >= max_refinements:
                break
            refinements += 1
            self._refinements = refinements
            self._set_status(
                "refining",
                f"Evaluation failed — refining (attempt {refinements})",
                kind="status",
            )

        # 6. Human approval
        self._set_status(
            "awaiting_approval",
            "Waiting for approval Signal (no polling process required)",
            kind="wait",
        )
        if auto_approve:
            self._approval = "approved"
            self._set_status(
                "awaiting_approval",
                "Auto-approved (no Signal wait)",
                kind="signal",
            )
        else:
            await workflow.wait_condition(lambda: self._approval is not None)

        if self._approval != "approved":
            self._set_status(
                "rejected",
                "Report rejected by human reviewer",
                kind="terminal",
            )
            return {
                "status": "rejected",
                "query": effective_query,
                "total_tokens": self._total_tokens,
            }

        self._set_status(
            "completed",
            f"Workflow completed · {self._total_tokens['total_tokens']} total tokens",
            kind="terminal",
        )
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
            "history": self._history[-40:],
        }
