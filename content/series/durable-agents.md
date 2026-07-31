---
title: Durable agents series
status: outline
audience: AI engineers building multi-step agents
style: context/STYLE.md
---

# Series: What breaks when your agent process dies?

Same agent. Two orchestration layers. One experiment.

| # | Post | Angle | Status | Draft |
|---|------|-------|--------|-------|
| 1 | Your agent is not durable (even with checkpoints) | Crash mid-write; partial recovery; token waste | ready | `drafts/01-not-durable-with-checkpoints.md` (+ social ready) |
| 2 | Human-in-the-loop should not require a live process | Polling SQLite vs Temporal Signals | ready | `drafts/02-hitl-without-polling.md` |
| 3 | Evaluation belongs inside the control flow | LLM-as-judge + refine as a real step | outline | `drafts/03-evaluation-in-the-loop.md` |
| 4 | Parallel tools, fair comparison | `asyncio.gather` vs concurrent Activities | idea | |
| 5 | Building the side-by-side lab | Repo architecture + experiment UI | draft | `drafts/04-side-by-side-lab.md` |
| 6 | Recording the proof | Loom script + shot list | deferred | `assets/loom-crash-demo.md` |

Series line: I built the same multi-agent research system twice (asyncio + checkpoints vs Temporal), then killed both mid-run. The delta is the curriculum.

## Assets

- Showcase mid-run + savings panel: `assets/media/2026-07-31-showcase-*.png` (P3.3)
- Temporal Web UI: `assets/media/2026-07-31-temporal-web-ui.png`
- Architecture: `assets/diagrams/02-shared-brain-two-runtimes.svg`
- Loom: deferred (P3.2)

## Distribution per post

Long-form draft here, then Substack/personal/Temporal blog; one LinkedIn cut; one short thread. Style stays `context/STYLE.md` in every channel.
