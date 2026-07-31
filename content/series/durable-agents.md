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
| 3 | Evaluation belongs inside the control flow | LLM-as-judge + refine as a real step | ready | `drafts/03-evaluation-in-the-loop.md` |
| 4 | Building the side-by-side lab | Repo architecture + experiment UI | ready | `drafts/04-side-by-side-lab.md` |
| 5 | Parallel tools only count if both stacks pay the same concurrency tax | `asyncio.gather` vs concurrent Activities; crash mid-search | ready | `drafts/05-parallel-tools-fair-comparison.md` (+ social ready) |
| 6 | Recording the proof | Loom script + shot list | ready (video in media/; narration optional) | `assets/loom-crash-demo.md` + `assets/media/2026-07-31-showcase-crash-demo.mp4` |
| — | What we leave incomplete on purpose (appendix) | Intentional recovery gaps on the non-Temporal path | ready | `drafts/recovery-gaps-on-purpose.md` + `concepts/recovery-gaps.md` |
| — | Crash-lab talk deck | 12-slide outline + asset map | ready (outline; pptx optional) | `decks/2026-07-31-durable-agents-crash-lab-outline.md` |

Series line: I built the same multi-agent research system twice (asyncio + checkpoints vs Temporal), then killed both mid-run. The delta is the curriculum.

## Assets

- Showcase mid-run + savings panel: `assets/media/2026-07-31-showcase-*.png` (P3.3)
- Temporal Web UI: `assets/media/2026-07-31-temporal-web-ui.png`
- Architecture: `assets/diagrams/02-shared-brain-two-runtimes.svg`
- Demo video (automated Showcase capture): `assets/media/2026-07-31-showcase-crash-demo.mp4` (P3.2)
- Loom shot list (optional narration): `assets/loom-crash-demo.md`

## Distribution per post

Long-form draft here, then Substack/personal/Temporal blog; one LinkedIn cut; one short thread. Style stays `context/STYLE.md` in every channel.
