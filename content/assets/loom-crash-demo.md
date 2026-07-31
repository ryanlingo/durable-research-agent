---
title: Crash demo recording script
status: draft
series: durable-agents
style: context/STYLE.md
duration: 90-120s
---

# Recording script: kill the agent, show what survives

A viewer should understand the thesis without reading the repo.

## Setup

1. `python -m ui.app`, Showcase mode, pace Talk
2. Experiment UI full screen
3. Optional second window: Temporal UI for a longer cut
4. Notifications off

## Shot list

| Time | Visual | Voice |
|------|--------|-------|
| 0:00-0:10 | UI header or dual pipelines idle | Same research agent, two stacks. Both get crashed mid-write. |
| 0:10-0:25 | Run experiment; pipeline advances | Clarify, plan, retrieve, search. Both healthy. |
| 0:25-0:40 | Crash on both columns | Process dies while writing the report. |
| 0:40-0:55 | Non-Temporal recovery events | Partial checkpoint recovery. In-flight work gone. Paid work runs again. |
| 0:55-1:10 | Temporal recovery events | Worker can die; Event History remains. Resume the unfinished Activity. |
| 1:10-1:25 | Token comparison bars | The reliability bug shows up as money. |
| 1:25-1:40 | Comparison headline | Retries and SQLite help. They are not Durable Execution. |

## Optional B-roll (3-minute cut)

CLI kill and restart of the non-Temporal run with `--run-id`. Temporal Web UI Event History after worker restart. Approval as poll loop versus Signal.

## Description paste

```
Same multi-step research agent twice: asyncio + checkpoints vs Temporal.
Crash both mid-write; compare recovery and token cost.

Repo: [link]
UI: python -m ui.app → Showcase
```

## Thumbnail

Dual pipelines. Left marked crashed / re-paid. Right marked resumed. Word on the image: TOKENS.
