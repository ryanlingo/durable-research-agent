---
title: Crash demo recording script
status: done
series: durable-agents
item: P3.2
duration: ~24s automated (or 90-120s with your voiceover)
video: content/assets/media/2026-07-31-showcase-crash-demo.mp4
---

# P3.2: crash demo recording

Automated capture is at `content/assets/media/2026-07-31-showcase-crash-demo.mp4` (no voiceover). Descriptive captions: `2026-07-31-showcase-crash-demo.vtt`. Local player: `content/assets/media/watch.html`. Use this script if you re-record with narration in Loom (pair with `2026-07-31-showcase-crash-demo-narration.vtt`).

**Feature:** Showcase UI runs both stacks through a mid-write crash.  
**Benefit:** Viewer sees lost work, re-paid tokens, and resume without reading code.  
**Outcome:** They understand why Durable Execution matters for agents.

Do not start screenshots or post polish until this recording is saved.

## Setup (once)

```bash
cd /Users/ryan/Desktop/durable-research-agent
source .venv/bin/activate
python -m ui.app
```

1. Open http://127.0.0.1:8765  
2. Mode: **Showcase (scripted crash)**  
3. Pace: **Talk**  
4. Auto-approve: on  
5. Browser full screen; quit notifications  
6. Cursor large enough to read on a laptop recording  

UI is already up if that URL loads.

## Record (one take, ~90–120s)

| Time | Do this | Say this |
|------|---------|----------|
| 0:00–0:10 | Dual columns idle on screen | Same research agent, two stacks. Both get crashed mid-write. |
| 0:10–0:25 | Click **Run experiment**. Watch pipelines advance | Clarify, plan, retrieve, search. Both healthy. |
| 0:25–0:40 | Point at crash / lost mid-write on both sides | Process dies while writing the report. |
| 0:40–0:55 | Left column recovery events | Partial checkpoint recovery. In-flight work gone. Paid work runs again. |
| 0:55–1:10 | Right column recovery events | Worker can die; Event History remains. Resume the unfinished Activity. |
| 1:10–1:25 | Token comparison bars | The reliability bug shows up as money. |
| 1:25–1:40 | Hold comparison headline | Retries and SQLite help. They are not Durable Execution. |

Stop. Do not add B-roll in this pass.

## Save

1. Export the Loom (or screen recording)  
2. Put a link (or file path) in `content/assets/media/LINKS.md`  
3. Tell me when it is done so we mark **P3.2 complete** and move to **P3.3 screenshots only**

## Description paste (Loom / YouTube)

```
Same multi-step research agent twice: asyncio + checkpoints vs Temporal.
Crash both mid-write; compare recovery and token cost.

Repo: https://github.com/ryanlingo/durable-research-agent
UI: python -m ui.app → Showcase
```

## Thumbnail

Dual pipelines. Left: crashed / re-paid. Right: resumed. Word on image: **TOKENS**.
