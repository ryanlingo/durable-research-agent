"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from ui.events import store


@pytest.fixture(autouse=True)
def _clear_ui_sessions() -> None:
    """Isolate UI session store between tests."""
    store._sessions.clear()
    yield
    for session in list(store._sessions.values()):
        session.closed = True
        for task in session.tasks.values():
            task.cancel()
    store._sessions.clear()
