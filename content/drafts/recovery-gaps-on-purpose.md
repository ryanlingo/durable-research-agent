---
title: What we leave incomplete on purpose
status: ready
series: durable-agents
post: appendix
style: context/STYLE.md
estimated_read: 5 min
repo: https://github.com/ryanlingo/durable-research-agent
---

# What we leave incomplete on purpose

A “fair” non-Temporal agent is easy to spoil in two directions. Make it a toy and Temporal looks inevitable. Perfect its resume path and you have rebuilt a workflow engine next to the model calls, then claimed the comparison still tests platforms.

This lab does neither. The typical stack has retries, stage checkpoints, resume by `run_id`, parallel search, evaluation, and human approval. It also has documented recovery gaps. Those gaps are the curriculum.

You want multi-step agents that survive production restarts without a re-run lottery. The concrete help is a checklist of what still breaks after “we added SQLite.” The feature is an intentional incomplete resume path in `without_temporal/agent.py`, paired with the same agent brain on Temporal.

## The gaps (short list)

Full catalog with code anchors: [`../concepts/recovery-gaps.md`](../concepts/recovery-gaps.md).

1. **Mid-write.** Draft checkpoints only after the LLM returns. Kill earlier and you rewrite; the provider may already have billed the dead call.  
2. **Mid-gather search.** `asyncio.gather` plus a post-batch checkpoint means partial search results die with the process.  
3. **Status strings.** Resume skips stages by coarse status, not a durable command log.  
4. **Re-eval.** Recovery can re-run the judge even when an evaluation row was hydrated.  
5. **Manual hydrate.** Nested results are rebuilt in application code. New fields mean new resume bugs.  
6. **Token lag.** Checkpoints understate spend for in-flight calls; `re_executed` only accounts re-pays after resume.

None of these are “we forgot.” Fixing all of them inside the agent process is how teams invent a private Temporal with worse observability.

## What fair still requires

Both stacks use the same tools, prompts, fixed RAG corpus, judge, and token counters. Both fan out search. Both have a human gate. Crash both at a named stage when you measure. If you disable concurrency only on the non-Temporal side, you are not measuring Durable Execution.

## How to see a gap without a lecture

```bash
python -m ui.app
# Showcase → Crash at: writing  → re-ran writing (+ often re-plan edge case)
# Showcase → Crash at: searching → gather boundary story
```

Live mode: crash non-Temporal mid-run, resume, read the “What re-ran” list and token gap. Temporal column streams Activity boundaries; completed work does not reappear as re-pays after Worker restart.

CLI: `demos/crash_demo.md`.

## Why this belongs next to the posts

Post 1 argued checkpoints are not Durable Execution. Post 5 argued parallel tools need the same fan-out on both sides. This note is the honesty clause: we kept realistic recovery pain so the Temporal path is not winning against a strawman, and we refused to paper over that pain with an infinite checklist of resume edge cases.

If your production agent already closed gap 1-6 with custom journals, you are in the market for a platform whether or not you use this repo’s stack names. If you have not, the token total after a forced crash is still the cheapest proof.

Lab: https://github.com/ryanlingo/durable-research-agent
