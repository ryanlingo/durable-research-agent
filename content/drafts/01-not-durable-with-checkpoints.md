---
title: Your agent is not durable (even with checkpoints)
status: draft
series: durable-agents
post: 1
style: context/STYLE.md
estimated_read: 8 min
---

# Your agent is not durable (even with checkpoints)

Retries and SQLite checkpoints do not make an agent durable. They make it slightly less fragile until the process dies mid-call, and then you find out how much of the control flow still lived only in memory.

**Outcome:** ship multi-step agents that survive restarts without turning every deploy into a re-run tax.  
**Benefit:** after a crash you can see what was lost, what was re-paid, and what Temporal reused from Event History.  
**Feature:** the same research agent twice (asyncio + checkpoints vs Workflow Execution + Activities), same tools and prompts.

I wanted that failure mode to be reproducible, not rhetorical. So I implemented the same multi-step research agent twice: once with asyncio, tenacity, and application-level checkpoints; once with Temporal (Workflow Definition, Activities, Signals, Queries, Event History). Same RAG corpus, tools, evaluation prompt, and token accounting. Only the orchestration layer changes. That constraint is the experiment. Terms follow Temporal’s glossary.

The agent does ordinary work. It decides whether the query needs clarification, plans a few search queries, retrieves from a fixed local corpus, runs web searches in parallel, writes a markdown report, scores faithfulness and relevance with an LLM judge, optionally refines once, then waits for human approval. If durability is messy here, it will be messier in a larger system.

## The crash

Use the same query on both stacks. Kill both runs at the same point, ideally while the report is being written, after plan, retrieve, and search have already spent tokens.

On the typical stack you reload the last checkpoint. The in-flight LLM result is gone. Tokens already billed to the provider may not match what your state file claims. Resume code has to reconstruct nested objects, decide which steps to skip, and hope you checkpointed the right fields. The recovery path you tested works; the edge you did not test is where production fails.

On Temporal a Worker Process can die without ending the Workflow Execution. That is Durable Execution: the run keeps its state through failures. Events land in Event History; on resume the history is replayed. Completed Activity results are reused, not recomputed. Incomplete work follows its Retry Policy.

The non-Temporal side is not a weak opponent. It has retries, checkpoints after major steps, and an approval gate. It still loses on resume correctness and on how much of the story you can inspect after a kill.

## Tokens as a reliability metric

After crash and restart, compare cumulative tokens for the same query.

The typical stack often pays again for work that looked saved: a partial write that never checkpointed, a re-plan because recovery restored too little, a full rewrite of the report. Temporal keeps completed Activities completed, so the bill tracks progress more than restart count.

If a crash doubles spend, the control plane is incomplete. That is a sharper signal than “we should add more logging.”

## Why checkpoints are not enough

Checkpointing is necessary and still application code. You decide when to write state, what to serialize, how to skip steps on resume, what happens to in-flight calls, and which process must stay alive while a human thinks. Each of those choices is a place agents shed correctness under load.

Durable Execution moves those problems into the platform: a Temporal Service plus workers. LLM and tool calls become Activities; their results land in history. You still design the agent. You stop re-implementing a half-finished workflow engine beside it.

## Seeing it

```bash
python -m ui.app
# http://127.0.0.1:8765 → Showcase → Run experiment
```

Showcase mode animates both paths through a mid-write crash without API keys. Use it for recordings. Live mode runs the real agents when you want production-shaped traces. CLI walkthrough: `demos/crash_demo.md`. After you restart the worker, the history is at http://localhost:8233.

Retries survive bad HTTP responses. They do not survive process death. Checkpoints help only as far as the recovery code you actually maintain. The token total after a forced crash is where that difference shows up without slogans.
