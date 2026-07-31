"""Token comparison helper (Temporal savings framing + re-ran list)."""

from ui.comparison import build_comparison


def test_temporal_savings_percent() -> None:
    c = build_comparison(6520, 4590, mode="showcase")
    assert c["wasted_tokens"] == 1930
    assert c["savings_percent"] == round(100.0 * 1930 / 6520, 1)
    assert "Temporal saved" in c["headline"]
    assert f"{c['savings_percent']:g}%" in c["headline"] or str(c["savings_percent"]) in c["headline"]
    assert c["bullets"][2].startswith("Temporal savings:")


def test_zero_gap_live_hints_crash() -> None:
    c = build_comparison(3000, 3000, mode="live")
    assert c["savings_percent"] == 0.0
    assert "same" in c["headline"].lower() or "Crash" in c["headline"]


def test_empty_totals() -> None:
    c = build_comparison(0, 0, mode="live")
    assert c["wasted_tokens"] == 0
    assert "No token totals" in c["headline"]


def test_re_executed_list_in_comparison() -> None:
    reruns = [
        {"step": "planning", "tokens": 610, "reason": "recovery edge case"},
        {"step": "writing", "tokens": 2400, "reason": "draft missing"},
    ]
    c = build_comparison(
        6520,
        4590,
        mode="showcase",
        re_executed=reruns,
        tokens_at_resume=3010,
    )
    assert c["re_executed_tokens"] == 3010
    assert c["re_executed_steps"] == ["planning", "writing"]
    assert c["tokens_at_resume"] == 3010
    assert any("What re-ran" in b for b in c["bullets"])
    assert any("3010" in b.replace(",", "") or "3,010" in b for b in c["bullets"])
    assert "re-paid" in c["headline"].lower() or "Re-paid" in c["headline"]
    assert c["re_executed"] == reruns
