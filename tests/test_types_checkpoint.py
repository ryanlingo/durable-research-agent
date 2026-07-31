"""Checkpoint serialization must be JSON-safe."""

import json

from shared.types import AgentState, SearchResult, TokenUsage


def test_checkpoint_serializes_nested_tokens() -> None:
    state = AgentState(query="test")
    state.search_results = [
        SearchResult(
            query="q",
            content="c",
            source="mock",
            tokens=TokenUsage(prompt_tokens=1, completion_tokens=2, total_tokens=3),
        )
    ]
    payload = state.checkpoint()
    # Must not raise
    raw = json.dumps(payload)
    assert "total_tokens" in raw
    assert payload["search_results"][0]["tokens"]["total_tokens"] == 3
