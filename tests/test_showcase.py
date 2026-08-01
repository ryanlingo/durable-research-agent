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
    expected_pct = round(100.0 * (w - t) / w, 1)
    assert snap["comparison"]["savings_percent"] == expected_pct
    assert expected_pct > 0
    assert "headline" in snap["comparison"]
    assert "Temporal saved" in snap["comparison"]["headline"]
    assert "%" in snap["comparison"]["headline"]
    # Crash script re-plans + rewrites on the non-Temporal side
    re_ran = snap["comparison"].get("re_executed") or []
    assert re_ran
    steps = {item["step"] for item in re_ran}
    assert "planning" in steps
    assert "writing" in steps
    assert snap["comparison"]["re_executed_tokens"] > 0
    assert snap["without"].get("re_executed")


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


@pytest.mark.asyncio
async def test_showcase_crash_at_evaluating() -> None:
    """Crash mid-eval: re-ran list includes evaluating; still shows Temporal savings."""
    session = store.create(query="crash at eval", mode="showcase", auto_approve=True)
    await run_showcase(session, crash_at="evaluating", pace=0.1)

    snap = session.snapshot()
    assert snap["without"]["status"] == "completed"
    assert snap["with"]["status"] == "completed"
    w = snap["without"]["tokens"]["total_tokens"]
    t = snap["with"]["tokens"]["total_tokens"]
    assert w > t
    steps = {item["step"] for item in snap["comparison"]["re_executed"]}
    assert "evaluating" in steps
    assert "planning" in steps  # incomplete recovery re-plan after plan was done
    assert "writing" not in steps  # write finished before crash


@pytest.mark.asyncio
async def test_showcase_crash_at_planning_no_double_plan() -> None:
    """Crash mid-plan: re-run planning once, not re-plan + re-run."""
    session = store.create(query="crash at plan", mode="showcase", auto_approve=True)
    await run_showcase(session, crash_at="planning", pace=0.1)

    snap = session.snapshot()
    re_ran = snap["comparison"]["re_executed"]
    plan_entries = [x for x in re_ran if x["step"] == "planning"]
    assert len(plan_entries) == 1
    assert snap["without"]["tokens"]["total_tokens"] > snap["with"]["tokens"]["total_tokens"]


@pytest.mark.asyncio
async def test_meta_exposes_crashable_stages() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        meta = await client.get("/api/meta")
        body = meta.json()
        assert "writing" in body["crashable_stages"]
        assert "evaluating" in body["crashable_stages"]
        assert body["default_crash_at"] == "writing"
        assert "completed" not in body["crashable_stages"]
        assert body.get("demo_video_url") == "/demo/watch.html"


@pytest.mark.asyncio
async def test_demo_video_player_routes() -> None:
    """Captioned demo is served from the UI app (not file://)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        watch = await client.get("/demo/watch.html")
        assert watch.status_code == 200
        assert b"Showcase crash demo" in watch.content
        mp4 = await client.get("/demo/2026-07-31-showcase-crash-demo.mp4")
        assert mp4.status_code == 200
        assert len(mp4.content) > 1000
        vtt = await client.get("/demo/2026-07-31-showcase-crash-demo.vtt")
        assert vtt.status_code == 200
        assert b"WEBVTT" in vtt.content
        redir = await client.get("/video", follow_redirects=False)
        assert redir.status_code in (307, 302)
        assert "/demo/watch.html" in redir.headers.get("location", "")


@pytest.mark.asyncio
async def test_invalid_crash_at_falls_back_to_writing() -> None:
    session = store.create(query="bad crash_at", mode="showcase", auto_approve=True)
    await run_showcase(session, crash_at="not-a-stage", pace=0.1)
    snap = session.snapshot()
    # Default writing crash still produces re-ran writing
    steps = {item["step"] for item in snap["comparison"]["re_executed"]}
    assert "writing" in steps
