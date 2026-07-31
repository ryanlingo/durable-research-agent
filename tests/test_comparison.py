"""Token comparison helper (Temporal savings framing)."""

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
