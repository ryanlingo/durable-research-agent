"""Non-Temporal recovery records re-executed steps and tokens."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from shared.types import EvaluationResult, TokenUsage
from without_temporal import state as wt_state
from without_temporal.agent import run_research


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "test_checkpoints.db"
    monkeypatch.setattr(wt_state, "DB_PATH", db)
    yield


def _usage(n: int = 100) -> TokenUsage:
    return TokenUsage(prompt_tokens=n // 2, completion_tokens=n - n // 2, total_tokens=n)


@pytest.mark.asyncio
async def test_rewrite_after_crash_mid_write_is_tracked() -> None:
    """Crash after searched (no draft) → resume re-writes and lists writing."""
    run_id = "resume-mid-write"
    # Simulate checkpoint after search, mid-write crash (draft never saved).
    from shared.types import AgentState, RetrievedChunk, SearchResult

    pre = AgentState(query="durable agents")
    pre.status = "searched"
    pre.clarified_query = "durable agents"
    pre.search_plan = ["q1", "q2"]
    pre.search_results = [
        SearchResult(query="q1", content="about durable execution"),
        SearchResult(query="q2", content="temporal activities"),
    ]
    pre.retrieved_chunks = [
        RetrievedChunk(doc_id="d1", title="T", content="Event History", score=0.9)
    ]
    pre.draft_report = None
    pre.total_tokens = _usage(1200)
    pre.history = [{"step": "searched", "ts": 1.0}]
    wt_state.save_state(run_id, pre.checkpoint())

    events: list[dict] = []

    async def on_event(payload: dict) -> None:
        events.append(payload)

    eval_result = EvaluationResult(
        faithfulness=0.95,
        relevance=0.95,
        overall=0.95,
        reasoning="ok",
        tokens=_usage(80),
    )

    with (
        patch(
            "without_temporal.agent._write_report",
            new=AsyncMock(return_value=("# Report\n\nGood.", _usage(500))),
        ),
        patch(
            "without_temporal.agent.evaluate_report",
            return_value=eval_result,
        ),
    ):
        report = await run_research(
            "durable agents",
            run_id=run_id,
            auto_approve=True,
            on_event=on_event,
        )

    assert report.total_tokens.total_tokens == 1200 + 500 + 80
    re_events = [e for e in events if e.get("type") == "re_executed"]
    assert re_events
    assert any(e.get("re_executed_step", {}).get("step") == "writing" for e in re_events)
    completed = next(e for e in events if e.get("type") == "completed")
    assert completed["re_executed_tokens"] >= 500
    steps = [x["step"] for x in completed["re_executed"]]
    assert "writing" in steps
    # First-time evaluation after rewrite should not count as re-ran
    assert "evaluating" not in steps


@pytest.mark.asyncio
async def test_reeval_after_resume_when_eval_saved() -> None:
    """Incomplete recovery re-runs judge when evaluation was already checkpointed."""
    run_id = "resume-reeval"
    from shared.types import AgentState, RetrievedChunk, SearchResult

    pre = AgentState(query="durable agents")
    pre.status = "awaiting_approval"
    pre.clarified_query = "durable agents"
    pre.search_plan = ["q1"]
    pre.search_results = [SearchResult(query="q1", content="ctx")]
    pre.retrieved_chunks = [
        RetrievedChunk(doc_id="d1", title="T", content="ctx", score=0.9)
    ]
    pre.draft_report = "# Already written"
    pre.evaluation = EvaluationResult(
        faithfulness=0.9,
        relevance=0.9,
        overall=0.9,
        reasoning="prior",
        tokens=_usage(70),
    )
    pre.approval_status = "pending"
    pre.total_tokens = _usage(2000)
    pre.history = [{"step": "awaiting_approval", "ts": 1.0}]
    wt_state.save_state(run_id, pre.checkpoint())

    events: list[dict] = []

    async def on_event(payload: dict) -> None:
        events.append(payload)

    eval_result = EvaluationResult(
        faithfulness=0.95,
        relevance=0.95,
        overall=0.95,
        reasoning="again",
        tokens=_usage(90),
    )

    with patch(
        "without_temporal.agent.evaluate_report",
        return_value=eval_result,
    ):
        report = await run_research(
            "durable agents",
            run_id=run_id,
            auto_approve=True,
            on_event=on_event,
        )

    assert report.total_tokens.total_tokens == 2000 + 90
    completed = next(e for e in events if e.get("type") == "completed")
    steps = [x["step"] for x in completed["re_executed"]]
    assert "evaluating" in steps
    assert "writing" not in steps  # draft was present
