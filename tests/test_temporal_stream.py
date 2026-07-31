"""Live Temporal event mapping (no Temporal server required)."""

from ui.temporal_stream import execution_status_event, history_item_to_event


def test_activity_complete_includes_token_delta() -> None:
    ev = history_item_to_event(
        {
            "status": "planned",
            "message": "Activity completed: plan_activity · 2 queries",
            "tokens": {"total_tokens": 150, "prompt_tokens": 100, "completion_tokens": 50},
            "token_delta": 40,
            "kind": "activity_complete",
            "activity": "plan_activity",
        },
        run_id="wf-1",
    )
    assert ev["side"] == "with"
    assert ev["type"] == "activity"
    assert ev["label"] == "activity"
    assert "+40 tokens" in ev["message"]
    assert ev["activity"] == "plan_activity"
    assert ev["status"] == "planned"


def test_activity_start_is_step() -> None:
    ev = history_item_to_event(
        {
            "status": "writing",
            "message": "Starting Activity: write_activity",
            "tokens": {"total_tokens": 200},
            "token_delta": 0,
            "kind": "activity_start",
            "activity": "write_activity",
        },
        run_id="wf-1",
    )
    assert ev["type"] == "step"
    assert ev["kind"] == "activity_start"


def test_wait_maps_to_awaiting_approval() -> None:
    ev = history_item_to_event(
        {
            "status": "awaiting_approval",
            "message": "Waiting for approval Signal",
            "kind": "wait",
            "token_delta": 0,
            "tokens": {"total_tokens": 900},
        },
        run_id="wf-1",
    )
    assert ev["type"] == "awaiting_approval"
    assert ev["label"] == "wait"


def test_signal_event() -> None:
    ev = history_item_to_event(
        {
            "status": "awaiting_approval",
            "message": "Received approval Signal: approved",
            "kind": "signal",
            "activity": "submit_approval",
            "token_delta": 0,
        },
        run_id="wf-1",
    )
    assert ev["type"] == "signal"
    assert "Signal" in ev["message"]


def test_execution_status_event() -> None:
    ev = execution_status_event(run_id="wf-1", execution_status="RUNNING")
    assert ev["type"] == "execution"
    assert "RUNNING" in ev["message"]
