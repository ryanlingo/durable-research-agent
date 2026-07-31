"""Showcase mode: dual crash script finishes with token comparison."""

from __future__ import annotations

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from ui.app import app
from ui.events import store
from ui.showcase import run_showcase


@pytest.mark.asyncio
async def test_run_showcase_completes_with_comparison() -> None:
    session = store.create(query="test durable agents", mode="showcase", auto_approve=True)
    await run_showcase(session, crash_at="writing", pace=0.15)

    snap = session.snapshot()
    assert snap["without"]["status"] == "completed"
    assert snap["with"]["status"] == "completed"
    w = snap["without"]["tokens"]["total_tokens"]
    t = snap["with"]["tokens"]["total_tokens"]
    assert w > t
    assert snap["comparison"]
    assert snap["comparison"]["without_tokens"] == w
    assert snap["comparison"]["with_tokens"] == t
    assert snap["comparison"]["wasted_tokens"] == w - t
    assert "headline" in snap["comparison"]


@pytest.mark.asyncio
async def test_showcase_api_session_lifecycle() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        meta = await client.get("/api/meta")
        assert meta.status_code == 200
        assert "showcase" in meta.json()["modes"]

        created = await client.post(
            "/api/sessions",
            json={
                "query": "api showcase smoke",
                "mode": "showcase",
                "pace": 0.15,
                "auto_approve": True,
            },
        )
        assert created.status_code == 200
        body = created.json()
        sid = body["session_id"]
        assert body["mode"] == "showcase"

        # Wait for both sides to complete (scripted, fast pace)
        for _ in range(80):
            resp = await client.get(f"/api/sessions/{sid}")
            assert resp.status_code == 200
            snap = resp.json()
            if (
                snap["without"]["status"] == "completed"
                and snap["with"]["status"] == "completed"
            ):
                break
            await asyncio.sleep(0.1)
        else:
            pytest.fail(f"showcase did not complete: {snap['without']['status']} / {snap['with']['status']}")

        assert snap["without"]["tokens"]["total_tokens"] > snap["with"]["tokens"]["total_tokens"]
        assert snap["comparison"]
        assert snap["comparison"].get("wasted_tokens", 0) >= 0

        stopped = await client.delete(f"/api/sessions/{sid}")
        assert stopped.status_code == 200
        missing = await client.get(f"/api/sessions/{sid}")
        assert missing.status_code == 404


@pytest.mark.asyncio
async def test_live_crash_endpoint_rejected_for_showcase() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        created = await client.post(
            "/api/sessions",
            json={"mode": "showcase", "pace": 0.15, "query": "x"},
        )
        sid = created.json()["session_id"]
        crash = await client.post(f"/api/sessions/{sid}/crash/without")
        assert crash.status_code == 400
        await client.delete(f"/api/sessions/{sid}")
