"""Post-run token comparison for Showcase and Live modes."""

from __future__ import annotations

from typing import Any


def build_comparison(
    without_tokens: int,
    with_tokens: int,
    *,
    mode: str = "showcase",
) -> dict[str, Any]:
    """Temporal savings vs non-Temporal bill: absolute tokens and percent."""
    w = max(0, int(without_tokens or 0))
    t = max(0, int(with_tokens or 0))
    saved = max(0, w - t)
    pct = round(100.0 * saved / w, 1) if w > 0 else 0.0

    if w == 0 and t == 0:
        headline = "No token totals yet on either side."
    elif saved == 0:
        headline = (
            f"Both sides used about the same tokens ({w:,} without, {t:,} with Temporal). "
            f"Crash and resume the non-Temporal run mid-flight to surface re-paid work."
            if mode == "live"
            else (
                f"Both sides ended near {w:,} tokens; no Temporal savings in this scripted run."
            )
        )
    else:
        headline = (
            f"Temporal saved ~{saved:,} tokens ({pct:g}% of the non-Temporal bill). "
            f"Non-Temporal spent {w:,}; Temporal spent {t:,}. "
            f"Completed Activities were not re-run after resume."
        )

    bullets = [
        f"Without Temporal: {w:,} total tokens",
        f"With Temporal: {t:,} total tokens",
        f"Temporal savings: {saved:,} tokens ({pct:g}%)",
    ]
    if mode == "live":
        bullets.append(
            "Live totals reflect real LLM/tool spend; crash non-Temporal mid-run to widen the gap."
        )
    else:
        bullets.append(
            "Showcase script forces a mid-write crash so re-paid work shows up on the left."
        )

    return {
        "without_tokens": w,
        "with_tokens": t,
        "wasted_tokens": saved,
        "savings_percent": pct,
        "headline": headline,
        "bullets": bullets,
        "mode": mode,
    }
