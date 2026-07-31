"""ResearchWorkflow tests with mocked Activities (no LLM / network)."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from with_temporal.workflows import ResearchWorkflow

TOKENS = {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

# Toggle for clarification-path test (single clarify Activity name).
_needs_clarification = False


@activity.defn(name="clarify_activity")
async def mock_clarify(query: str) -> dict[str, Any]:
    if _needs_clarification:
        return {
            "needs_clarification": True,
            "questions": ["What scope?"],
            "reason": "ambiguous",
            "_tokens": TOKENS,
        }
    return {"needs_clarification": False, "_tokens": TOKENS}

@activity.defn(name="plan_activity")
async def mock_plan(query: str) -> dict[str, Any]:
    return {"plan": ["q1", "q2"], "_tokens": TOKENS}


@activity.defn(name="retrieve_activity")
async def mock_retrieve(query: str) -> dict[str, Any]:
    return {
        "chunks": [
            {"doc_id": "d1", "title": "T", "content": "durable execution context", "score": 0.9}
        ],
        "_tokens": TOKENS,
    }


@activity.defn(name="search_activity")
async def mock_search(query: str) -> dict[str, Any]:
    return {
        "query": query,
        "content": f"search hits for {query}",
        "source": "mock",
        "_tokens": TOKENS,
    }


@activity.defn(name="write_activity")
async def mock_write(query: str, search_results: list, chunks: list) -> dict[str, Any]:
    return {"report": f"# Report\n\nAnswer for: {query}", "_tokens": TOKENS}


@activity.defn(name="evaluate_activity")
async def mock_evaluate(query: str, report: str, context_chunks: list[str]) -> dict[str, Any]:
    return {
        "faithfulness": 0.95,
        "relevance": 0.95,
        "overall": 0.95,
        "reasoning": "Grounded in context.",
        "passed": True,
        "_tokens": TOKENS,
    }


MOCK_ACTIVITIES = [
    mock_clarify,
    mock_plan,
    mock_retrieve,
    mock_search,
    mock_write,
    mock_evaluate,
]

@pytest.mark.asyncio
async def test_workflow_auto_approve_completes() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-research",
            workflows=[ResearchWorkflow],
            activities=MOCK_ACTIVITIES,
        ):
            result = await env.client.execute_workflow(
                ResearchWorkflow.run,
                args=["How does durable execution help?", True, 1],
                id="test-auto-approve",
                task_queue="test-research",
                execution_timeout=timedelta(seconds=30),
            )

    assert result["status"] == "completed"
    assert "Report" in result["markdown_report"]
    assert result["evaluation"]["overall"] == 0.95
    assert result["total_tokens"]["total_tokens"] > 0
    assert result["refinements"] == 0


@pytest.mark.asyncio
async def test_workflow_status_query_and_approval_signal() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-research-hitl",
            workflows=[ResearchWorkflow],
            activities=MOCK_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                ResearchWorkflow.run,
                args=["HITL query", False, 1],
                id="test-hitl-approval",
                task_queue="test-research-hitl",
                execution_timeout=timedelta(seconds=30),
            )

            # Wait until workflow is awaiting approval
            for _ in range(100):
                st = await handle.query(ResearchWorkflow.status)
                if st.get("waiting_for_approval") or st.get("status") == "awaiting_approval":
                    break
                await asyncio.sleep(0.05)
            else:
                st = await handle.query(ResearchWorkflow.status)
                pytest.fail(f"never reached awaiting_approval: {st}")

            st = await handle.query(ResearchWorkflow.status)
            assert st["waiting_for_approval"] is True
            assert st["total_tokens"]["total_tokens"] > 0
            assert st["search_plan"] == ["q1", "q2"]

            await handle.signal(ResearchWorkflow.submit_approval, "approved")
            result = await handle.result()

    assert result["status"] == "completed"
    assert result["evaluation"]["overall"] == 0.95


@pytest.mark.asyncio
async def test_workflow_rejection() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-research-reject",
            workflows=[ResearchWorkflow],
            activities=MOCK_ACTIVITIES,
        ):
            handle = await env.client.start_workflow(
                ResearchWorkflow.run,
                args=["Reject me", False, 1],
                id="test-reject",
                task_queue="test-research-reject",
                execution_timeout=timedelta(seconds=30),
            )
            for _ in range(100):
                st = await handle.query(ResearchWorkflow.status)
                if st.get("status") == "awaiting_approval":
                    break
                await asyncio.sleep(0.05)
            await handle.signal(ResearchWorkflow.submit_approval, "rejected")
            result = await handle.result()

    assert result["status"] == "rejected"


@pytest.mark.asyncio
async def test_workflow_auto_approve_skips_clarification_wait() -> None:
    """needs_clarification + auto_approve should not hang on a Signal."""
    global _needs_clarification
    _needs_clarification = True
    try:
        async with await WorkflowEnvironment.start_time_skipping() as env:
            async with Worker(
                env.client,
                task_queue="test-research-clarify",
                workflows=[ResearchWorkflow],
                activities=MOCK_ACTIVITIES,
            ):
                result = await env.client.execute_workflow(
                    ResearchWorkflow.run,
                    args=["vague query", True, 1],
                    id="test-auto-clarify",
                    task_queue="test-research-clarify",
                    execution_timeout=timedelta(seconds=30),
                )
    finally:
        _needs_clarification = False

    assert result["status"] == "completed"
    assert "Clarification" in result["query"]
