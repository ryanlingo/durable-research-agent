---
title: Crash and resume the non-Temporal agent (CLI)
status: ready
estimated_time: 10 min
prereq: OPENAI_API_KEY in .env for a live run; or read along with Showcase only
---

# Crash and resume the non-Temporal agent (CLI)

| Layer | |
|-------|--|
| **Feature** | Kill `without_temporal` mid-run and resume with the same `run_id` |
| **Benefit** | Feel incomplete checkpoint recovery and re-paid steps on a real process |
| **Outcome** | Know what “we save checkpoints” actually means when the process dies |

For a zero-key version of the same story, use [Showcase](01-showcase-ui.md). This tutorial is the production-shaped path: real process, SQLite, resume flag.

## Setup

```bash
cd durable-research-agent
source .venv/bin/activate
cp -n .env.example .env   # set OPENAI_API_KEY
pip install -r requirements.txt
```

## Terminal 1: start a run

```bash
python -m without_temporal.run \
  "How does durable execution help AI agents survive process crashes?" \
  --auto-approve
```

Note the printed `run_id=` line at the start. Leave the process running until you see a late checkpoint such as `checkpointed at 'searched'` or `Writing draft report`.

## Terminal 2: kill the process

```bash
pkill -f "without_temporal.run"
```

If `pkill` is unavailable, interrupt the process with Ctrl+C in terminal 1 (less realistic than a hard kill, still enough to practice resume).

## Terminal 1: resume with the same run_id

```bash
python -m without_temporal.run \
  "How does durable execution help AI agents survive process crashes?" \
  --run-id <RUN_ID> \
  --auto-approve
```

## What to observe

1. Log line about partial recovery from a checkpoint and the recovered `status`.  
2. Whether the draft was present. Mid-write kills usually force a rewrite.  
3. Token total at the end vs a clean run without a kill (same query).  
4. Intentional gaps: mid-gather search, re-eval, coarse status. Catalog: [`../concepts/recovery-gaps.md`](../concepts/recovery-gaps.md).

## Optional: human approval instead of auto-approve

Omit `--auto-approve`. When the agent waits:

```bash
python -m without_temporal.approve <RUN_ID> approved
```

The process polls SQLite every two seconds. That is the non-durable HITL shape (post 02).

## UI alternative (Live mode)

```bash
python -m ui.app
```

Mode **Live**, start a session, **Crash non-Temporal**, then **Resume non-Temporal**. Requires API key; Temporal column needs server + worker (tutorial 03) if you run both sides.

## Next

- Temporal Worker kill: [`03-crash-with-temporal.md`](03-crash-with-temporal.md)  
- Dual one-pager: [`../../demos/crash_demo.md`](../../demos/crash_demo.md)  
