---
title: Parallel tools only count if both stacks pay the same concurrency tax
status: ready
series: durable-agents
post: 5
style: context/STYLE.md
estimated_read: 6 min
repo: https://github.com/ryanlingo/durable-research-agent
---

# Parallel tools only count if both stacks pay the same concurrency tax

If one side runs searches one after another and the other fans them out, you are not measuring Durable Execution. You are measuring who wrote a faster loop.

You want multi-step agents that call tools in parallel without turning crash recovery into guesswork. The concrete help is knowing, after a kill mid-search, which results you can trust and which work you will re-pay. The feature is the same parallel search step implemented twice in this lab: `asyncio.gather` on the typical stack, concurrent Activities on Temporal.

This is post 5 of a series that runs one research agent on two control planes. Posts 1-4 covered crash recovery, human approval, evaluation in the loop, and the lab layout. Here the subject is parallel tools, and the fairness rule that makes the comparison honest.

## Same fan-out, two runtimes

After planning, both paths run a short list of web search queries at once. Shared helpers do the actual search. Only orchestration differs.

Typical stack (`without_temporal/agent.py`): build a coroutine per query, then `asyncio.gather`. Results land in process memory. The SQLite checkpoint for `searched` runs after the gather finishes. If the process dies mid-gather, intermediate results that never returned do not hit the checkpoint. Resume often re-runs the whole batch.

Temporal (`with_temporal/workflows.py`): for each query, `workflow.start_activity(search_activity, …)`, then await the handles. Each search is its own Activity with a Retry Policy. When an Activity completes, its result is recorded in Event History. A Worker restart does not invent those results again. Incomplete Activities retry; finished ones stay finished on replay.

Both are parallel. Both use the same search tool. Fairness means the non-Temporal side is not sequential “to keep the demo simple.” If you under-power the typical stack, Temporal always “wins” for the wrong reason.

## Why gather feels fine until it does not

`asyncio.gather` is the right default in a single process. Latency drops. Code stays short. For agents that call three or four tools before writing a report, that is normal production shape.

The durability problem is not concurrency. It is the boundary. Gather returns when the whole group finishes (or fails, depending on flags). Your checkpoint, if you write one, usually sits after that boundary. Crash timing decides whether you keep zero of the in-flight results or all of them. Partial progress inside the gather is not a first-class resume unit unless you built that yourself: per-query rows, locks, merge logic, skip sets.

Temporal’s unit is the Activity. Parallelism is concurrent Activities, not a single opaque batch. That is Feature language. The Benefit is practical: after a Worker dies mid-search, completed searches do not re-bill on Event History replay. The Outcome is an agent pipeline you can kill during tool fan-out without treating every parallel step as an all-or-nothing lottery.

## Fair comparison is a design rule

Side-by-side labs fail quietly when only one path is concurrent, cached, or auto-approved. This repo’s rule is boring on purpose:

1. Same tools, prompts, corpus, judge, and token counters  
2. Same pipeline stages, including parallel search  
3. Same human gate (poll vs Signal; both real)  
4. Crash both at a named stage when you measure  

If you change only durability and control flow, token gaps after a crash mean something. If you also change concurrency, you mixed variables.

The Showcase UI can crash mid-search as well as mid-write. Live mode streams Temporal Activity start/complete events so the concurrent search step is visible, not buried in a single “searching…” line.

![Agent pipeline including parallel search](../assets/diagrams/06-pipeline-linear.svg)

## Crash at searching, not only at writing

Post 1 used mid-write as the default story because the token gap is large and easy to see. Mid-search is the parallel lesson.

On the typical stack, kill during gather and you often resume from the last checkpoint before search (for example `planned` or after retrieve). You re-issue every query in the plan. Any search that had already returned in the dead process is gone unless you checkpointed per result.

On Temporal, kill the Worker while searches are in flight. Completed `search_activity` results remain in Event History. Incomplete ones retry under policy. You do not re-plan or re-retrieve because those Activities already finished.

Tokens after resume track that difference. Parallelism without durable boundaries multiplies re-paid work: three concurrent calls can become three re-pays, not one.

## What this is not claiming

Temporal does not make tools free. Concurrent Activities still spend tokens and still hit rate limits. Retries still cost money when the tool fails. The claim is narrower: when you already need parallel tools, Durable Execution gives you a resume unit smaller than “the whole gather,” and a fair lab must give the non-Temporal path the same concurrency so that claim is the only variable left.

## Seeing it

```bash
python -m ui.app
# Showcase → Crash at: searching → Run
```

Watch both columns enter searching together. After the scripted crash, compare which side re-runs paid work and what the savings panel reports. Live mode with a Worker shows Activity-level events for concurrent searches.

CLI walkthrough for process kills: `demos/crash_demo.md`. Lab: https://github.com/ryanlingo/durable-research-agent

Parallel tools are table stakes for agents. Parallel tools with crash semantics you can explain are the actual design problem. Fair comparison is how you stop lying to yourself about which part of the stack is saving you.
