# 30-minute interview / demo playbook

Run-of-show for a hiring manager, staff engineer, or Temporal-adjacent interview. Goal: they leave with **evidence** (tokens, re-ran work, Worker vs Execution), not a slogan about reliability.

| Layer | |
|-------|--|
| **Feature** | Timed script: Showcase crash, savings panel, optional Live or CLI, one diagram |
| **Benefit** | You can demo the lab cold in half an hour without hunting files |
| **Outcome** | They can decide if durable control flow belongs in multi-step agents |

**Default mode is Showcase (no API keys).** Live and CLI are stretch goals if time and keys allow.

---

## Before the call (5 min, once)

```bash
cd durable-research-agent
source .venv/bin/activate
pip install -r requirements.txt
python -m ui.app          # http://127.0.0.1:8765
```

On the UI, click **Interview demo** (Showcase · talk pace · crash at writing · Run),
or set those controls manually. Captioned fallback video: `/demo/watch.html`.

Optional: open the deck  
`content/decks/2026-07-31-durable-agents-crash-lab.pptx`

Optional: captioned video player (UI must be running)  
http://127.0.0.1:8765/demo/watch.html  
(mp4 also at `content/assets/media/2026-07-31-showcase-crash-demo.mp4` for VLC)

Browser: full screen UI, quit notifications. Repo tab open on README.

---

## Minute map (30 min)

| Min | Block | You do | They should take away |
|-----|--------|--------|------------------------|
| 0–2 | Claim | One sentence (below) | Why we are here |
| 2–4 | Setup | Same agent, two stacks (table) | Fair comparison |
| 4–12 | **Showcase live** | Run mid-write crash | Process death is the bug |
| 12–16 | Savings | Panel + what re-ran | Tokens = reliability metric |
| 16–20 | Temporal terms | Worker ≠ Execution; Event History | Glossary sticks |
| 20–24 | Fairness / gaps | One intentional gap | Not a strawman |
| 24–28 | Stretch or Q&A | Live crash *or* questions | Depth |
| 28–30 | Close + links | Repo, tutorials, post 01 | How to go deeper |

If the room is 15 minutes: do **0–16 only** (claim → Showcase → savings), skip stretch.

---

## Lines to say

**Open (0–2)**

> Retries and SQLite checkpoints do not make an agent durable. They make it slightly less fragile until the process dies mid-call. I built the same research agent twice and crashed both mid-write. We measure the difference in tokens.

**Stacks (2–4)**

> Same tools, prompts, RAG, judge, token counters. Left: asyncio, tenacity, SQLite, polling approval. Right: Workflow Execution, Activities, Signals, Event History. Only the control plane changes.

**During Showcase (4–12)**

1. Mode **Showcase**, Crash at **writing**, Pace **Talk** (or **Fast** if short on time).  
2. Click **Run**. Stay quiet while pipelines move.  
3. On crash:  
   - Left: process killed; partial recovery; re-paid work.  
   - Right: Worker can die; history retained; completed Activities not re-run.  
4. When the comparison appears, stop.

**Savings (12–16)**

> Scripted mid-write: about 6,520 tokens without Temporal, 4,590 with. Savings about 1,930 tokens, roughly 30% of the non-Temporal bill. The UI lists what re-ran on the left. Reliability shows up as money.

**Terms (16–20)** (optional diagram: `content/assets/diagrams/04-crash-with-temporal.svg`)

> Killing the Worker Process is not killing the Workflow Execution. Event History records completed Activities. On resume, history is replayed; finished work is not recomputed.

**Fairness (20–24)**

> The left side is not a toy. It has retries, checkpoints, parallel search, and approval. We also leave intentional resume gaps (mid-write draft boundary, mid-gather search) so we do not pretend SQLite equals Durable Execution. Catalog: `content/concepts/recovery-gaps.md`.

**Close (28–30)**

> If a crash doubles spend, the control plane is incomplete. That is sharper than "add more logging." Clone the repo, run Showcase, read post 01.

---

## Stretch (if time + keys)

### A. Live UI crash (tutorial 04)

Needs: `.env` with `OPENAI_API_KEY`, `temporal server start-dev`, `python -m with_temporal.worker`.

1. Mode **Live**, Auto-approve on, **Run**.  
2. Mid-writing on the left: **Crash non-Temporal** → **Resume non-Temporal**.  
3. Point at re-ran events and real token totals.  

### B. Worker kill (tutorial 03)

While Temporal is mid-run: `pkill -f with_temporal.worker`, restart worker, show Web UI Event History at http://localhost:8233.

### C. Deck only (no live UI)

Walk slides 1–7 and 12 from `content/decks/2026-07-31-durable-agents-crash-lab.pptx`. Play the mp4 on the demo beat.

---

## Hand them after

| Asset | Path |
|-------|------|
| Repo | https://github.com/ryanlingo/durable-research-agent |
| Showcase tutorial | `content/tutorials/01-showcase-ui.md` |
| Live tutorial | `content/tutorials/04-live-mode.md` |
| Post 01 (crash) | `content/drafts/01-not-durable-with-checkpoints.md` |
| Recovery gaps | `content/concepts/recovery-gaps.md` |
| Social launch paste | `content/social/launch-thread.md` |
| Full tutorial index | `content/tutorials/README.md` |

---

## Failure modes (have a backup)

| Problem | Fallback |
|---------|----------|
| UI will not start | Play `2026-07-31-showcase-crash-demo.mp4` (+ `.vtt` captions) or `watch.html` + deck |
| Showcase hangs | Stop, restart UI, Pace **Fast** |
| No network for clone story | Local repo already open; screenshots in `content/assets/media/` |
| They only care about HITL | Jump to diagram `05-hitl-polling-vs-signal.svg` + post 02 |

---

## One-page cheat sheet (print or second screen)

```
CLAIM   Checkpoints ≠ Durable Execution
DEMO    ui.app → Showcase → Crash at writing → Run
NUMBER  ~6520 vs ~4590 tokens (~30% savings)
TERMS   Worker Process ≠ Workflow Execution; Event History
LEFT    Re-ran list / incomplete recovery
RIGHT   Completed Activities not re-executed
CLOSE   github.com/ryanlingo/durable-research-agent
```
