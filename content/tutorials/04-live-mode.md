---
title: Live mode (real agents, Crash / Resume, Temporal stream)
status: ready
estimated_time: 20 min
prereq: OPENAI_API_KEY, Temporal CLI, Worker Process, experiment UI
---

# Live mode (real agents, Crash / Resume, Temporal stream)

| Layer | |
|-------|--|
| **Feature** | Experiment UI **Live** mode: real LLM/tool runs on both stacks, Crash/Resume on non-Temporal, Activity-level events on Temporal |
| **Benefit** | See a real token gap and re-ran list after a mid-flight kill, not only the scripted Showcase numbers |
| **Outcome** | Prove the lab on your machine with production-shaped spend and Event History |

Showcase (tutorial 01) needs no keys. Live mode spends API tokens and needs a Temporal Service + Worker for the right column.

Terms: [`../concepts/temporal-concepts.md`](../concepts/temporal-concepts.md).

## What you need

1. OpenAI key in `.env`  
2. Temporal CLI (`temporal server start-dev`)  
3. Repo deps installed  

```bash
cd durable-research-agent
source .venv/bin/activate
cp -n .env.example .env   # set OPENAI_API_KEY
pip install -r requirements.txt
```

## Terminals (keep them open)

### A. Temporal Service

```bash
temporal server start-dev
```

Web UI: [http://localhost:8233](http://localhost:8233).

### B. Worker Process

```bash
python -m with_temporal.worker
# or: make worker
```

### C. Experiment UI

```bash
python -m ui.app
# or: make demo
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Path A: clean dual run (baseline)

1. **Mode:** Live  
2. **Auto-approve:** checked  
3. Leave the default query (or paste your own).  
4. Click **Run**.  

**Crash at** is Showcase-only; it is hidden in Live mode.

### Watch the columns

| Side | Expect |
|------|--------|
| **Without Temporal** | Steps and checkpoints; token total climbs; recovery label is checkpoints |
| **With Temporal** | Events labeled activity / wait / signal / execution; token total climbs; Workflow ID appears |

Right-column events come from Workflow status Queries (application history: Activity start/complete, waits), plus Workflow Execution status from `describe`. That is richer than a single “searching…” line; it is still not a dump of every Temporal Event History record (use the Web UI for that).

When both complete, the **After the crash** panel may still appear with totals. On a clean run (no kill) savings can be near zero: that is expected. The gap widens when you crash and resume the left side.

## Path B: crash non-Temporal mid-run (the point of Live)

1. Start Live again (Path A setup).  
2. When the left column is in **searching**, **writing**, or **evaluating** (tokens moving, status not idle):  
   - Click **Crash non-Temporal**  
3. Left status should show crashed; tokens freeze at the last published total.  
4. Click **Resume non-Temporal**.  

### What to observe after resume

1. **Recovered** event: checkpoint status, draft present or missing.  
2. **re_executed** / re-ran steps when recovery re-pays work (rewrite if draft missing; sometimes re-eval).  
3. Final left token total **above** a clean run of the same query.  
4. Right column: Temporal should keep progressing (or already finished). Completed Activities do not reappear as re-pays on the left’s crash.  
5. When both sides reach a terminal state, comparison shows **Temporal savings** and **What re-ran (without Temporal)** if re-pays were recorded.

Intentional gaps (mid-write, mid-gather, re-eval): [`../concepts/recovery-gaps.md`](../concepts/recovery-gaps.md).

## Path C: optional HITL (no auto-approve)

1. Uncheck **Auto-approve**.  
2. Run Live.  
3. When a side waits for approval:  
   - **Approve (without)** for the SQLite poll path  
   - **Approve (Temporal)** sends a **Signal** into the Workflow Execution  

If you leave auto-approve off and never approve, that side stays waiting. That is the lesson for post 02 (poll vs Signal).

## Path D: Worker dies during Live (advanced)

While both columns are running:

```bash
pkill -f "with_temporal.worker"
```

Temporal progress in the UI may stall or show Query errors. Restart:

```bash
python -m with_temporal.worker
```

The **Workflow Execution** continues; completed Activities are not re-executed on Event History replay. Confirm in [http://localhost:8233](http://localhost:8233). Longer CLI version: [`03-crash-with-temporal.md`](03-crash-with-temporal.md).

## Troubleshooting

| Symptom | Check |
|---------|--------|
| Right column: cannot connect to Temporal | Terminal A running? Host `localhost:7233`? |
| Right column stuck after start | Worker (terminal B) running? Task queue logs? |
| Left column errors on LLM | `OPENAI_API_KEY` in `.env`? Model name in config? |
| Comparison never appears | Wait for both sides terminal (completed/error). After crash, **Resume** first. |
| No re-ran list | Crash mid-write (draft not checkpointed) or resume paths that re-eval; clean runs have nothing to re-pay. |

## How Live differs from Showcase

| | Showcase | Live |
|--|----------|------|
| Keys / Temporal Service | No | Yes (for Temporal column) |
| Crash point | **Crash at** selector | **Crash non-Temporal** button (timing is yours) |
| Tokens | Scripted | Real provider usage |
| Temporal events | Scripted | Queries + Execution status |

Use Showcase for talks and zero-key demos. Use Live when you need a real bill and a real Workflow Execution.

## Next

- Showcase only: [`01-showcase-ui.md`](01-showcase-ui.md)  
- CLI non-Temporal crash: [`02-crash-without-temporal.md`](02-crash-without-temporal.md)  
- CLI Temporal Worker kill: [`03-crash-with-temporal.md`](03-crash-with-temporal.md)  
- Dual one-pager: [`../../demos/crash_demo.md`](../../demos/crash_demo.md)  
- Talk deck: [`../decks/2026-07-31-durable-agents-crash-lab.pptx`](../decks/2026-07-31-durable-agents-crash-lab.pptx)  

Lab: https://github.com/ryanlingo/durable-research-agent
