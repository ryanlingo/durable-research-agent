"""Post-run token comparison for Showcase and Live modes."""

from __future__ import annotations

from typing import Any


def build_comparison(
    without_tokens: int,
    with_tokens: int,
    *,
    mode: str = "showcase",
    re_executed: list[dict[str, Any]] | None = None,
    tokens_at_resume: int | None = None,
) -> dict[str, Any]:
    """Temporal savings vs non-Temporal bill: absolute tokens and percent.

    Optional re_executed: list of {step, tokens, reason} from non-Temporal
    recovery — the work that ran again after a crash/resume.
    """
    w = max(0, int(without_tokens or 0))
    t = max(0, int(with_tokens or 0))
    saved = max(0, w - t)
    pct = round(100.0 * saved / w, 1) if w > 0 else 0.0

    reruns = list(re_executed or [])
    re_tokens = sum(int(x.get("tokens", 0) or 0) for x in reruns)
    re_steps = [str(x.get("step", "?")) for x in reruns]

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
        if re_tokens > 0:
            headline += f" Non-Temporal re-paid ~{re_tokens:,} tokens after resume."

    bullets = [
        f"Without Temporal: {w:,} total tokens",
        f"With Temporal: {t:,} total tokens",
        f"Temporal savings: {saved:,} tokens ({pct:g}%)",
    ]
    if tokens_at_resume is not None and int(tokens_at_resume) > 0:
        bullets.append(
            f"Non-Temporal tokens at resume checkpoint: {int(tokens_at_resume):,}"
        )
    if reruns:
        step_bits = []
        for item in reruns:
            step = item.get("step", "?")
            tok = int(item.get("tokens", 0) or 0)
            step_bits.append(f"{step} (+{tok:,})" if tok else str(step))
        bullets.append(
            f"What re-ran without Temporal: {', '.join(step_bits)} "
            f"· {re_tokens:,} tokens re-paid"
        )
    elif mode == "live":
        bullets.append(
            "Live totals reflect real LLM/tool spend; crash non-Temporal mid-run "
            "to widen the gap and list re-ran steps."
        )
    else:
        bullets.append(
            "Showcase script forces a mid-write crash so re-paid work shows up on the left."
        )

    if mode == "live" and not reruns and saved > 0:
        bullets.append(
            "Gap may include partial in-flight bills; re-ran list fills in after resume."
        )

    return {
        "without_tokens": w,
        "with_tokens": t,
        "wasted_tokens": saved,
        "savings_percent": pct,
        "headline": headline,
        "bullets": bullets,
        "mode": mode,
        "re_executed": reruns,
        "re_executed_tokens": re_tokens,
        "re_executed_steps": re_steps,
        "tokens_at_resume": tokens_at_resume,
    }
