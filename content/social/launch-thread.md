---
title: Launch thread and LinkedIn
status: ready
source: drafts/01-not-durable-with-checkpoints.md
style: context/STYLE.md
repo: https://github.com/ryanlingo/durable-research-agent
media:
  - ../assets/media/2026-07-31-showcase-mid-run.png
  - ../assets/media/2026-07-31-showcase-comparison-panel.png
---

# How to post

1. Attach mid-run UI + savings panel (or full comparison page).
2. Paste X thread as a thread; paste LinkedIn as one post.
3. Link the repo once at the end of each.

Do not wait on the Loom. Post 01 is ready if you want a longer link later.

---

# X thread

1/ Retries and SQLite checkpoints do not make an agent durable. They make it slightly less fragile until the process dies mid-call.

2/ I built the same multi-step research agent twice: asyncio + tenacity + SQLite checkpoints, and Temporal (Workflow Execution, Activities, Signals).

Same tools, prompts, RAG, judge, and token counters. Only orchestration changes. Then both get crashed mid-write.

3/ Non-Temporal side is not a strawman. It has retries, checkpoints, and an approval gate.

It still loses the in-flight draft. Recovery is incomplete by default. You often re-pay work you thought you saved.

4/ Temporal: the Worker can die; the Workflow Execution does not. Event History is replayed. Completed Activities are not re-run.

5/ Scripted Showcase numbers (same crash story, no API keys):

Without Temporal: ~6,520 tokens  
With Temporal: ~4,590 tokens  
Temporal savings: ~1,930 tokens (29.6% of the non-Temporal bill)

6/ Reliability shows up on the invoice. If a crash doubles spend, the control plane is incomplete.

7/ Dual-column experiment UI is in the repo. Showcase mode needs no API keys and no Temporal server.

https://github.com/ryanlingo/durable-research-agent

8/ Retries ≠ durability. Checkpoints ≠ Durable Execution.

---

# LinkedIn

Retries and SQLite checkpoints do not make an agent durable. They make it slightly less fragile until the process dies mid-call.

I built the same multi-step research agent twice: once with asyncio, tenacity, SQLite checkpoints, and polling approval; once with Temporal (Workflow Execution, Activities, Signals, Event History). Same tools, prompts, RAG, and token counters. Only the control plane changes. Then both get crashed mid-write.

The non-Temporal path still does the responsible things. Recovery is still partial. In-flight LLM work is still gone. The token bill still climbs.

The Temporal path resumes by replaying Event History. Completed Activities are not re-run. Human approval is a Signal, not a live polling process.

In the scripted Showcase demo (forced mid-write crash): non-Temporal ~6,520 tokens, Temporal ~4,590. Temporal savings ~1,930 tokens, about 29.6% of the non-Temporal bill.

The metric that travels: tokens after crash-and-restart.

Lab, dual-pipeline UI, and write-up:

https://github.com/ryanlingo/durable-research-agent

Attach: side-by-side mid-run UI + “Temporal saved … 29.6%” panel.
