---
title: Post 05 social cuts: parallel tools
status: ready
source: drafts/05-parallel-tools-fair-comparison.md
style: context/STYLE.md
repo: https://github.com/ryanlingo/durable-research-agent
---

# How to post

1. Optional image: pipeline diagram or Live Temporal events during searching.
2. X as a short thread; LinkedIn as one post.
3. Link the repo once.

---

# X thread

1/ If one agent path runs tools in parallel and the other is sequential, you are not measuring Durable Execution. You are measuring who wrote a faster loop.

2/ In the durable research lab, both stacks fan out web search the same way: asyncio.gather on the typical path, concurrent Activities on Temporal. Same tool, same queries.

3/ gather is fine until the process dies mid-batch. Your checkpoint usually sits after the whole group finishes. Partial results in the dead process do not become a resume unit for free.

4/ Concurrent Activities do. Completed searches stay in Event History. Incomplete ones retry. You do not re-pay finished work when the Worker restarts.

5/ Fair comparison is the design rule: same tools, same parallel stage, same crash point. Then token gaps mean something.

Lab: https://github.com/ryanlingo/durable-research-agent

---

# LinkedIn

If one “agent demo” fans tools out and the other runs them in a for-loop, the durability story is already contaminated.

I run the same multi-step research agent twice. Both paths plan a few web searches and execute them in parallel: `asyncio.gather` without Temporal, concurrent Activities with Temporal. Shared tools and prompts. The only intended variable is the control plane.

That matters at crash time. Gather plus a checkpoint after the batch is an all-or-nothing resume boundary unless you invent per-query state. Concurrent Activities give you a smaller unit: finished searches stay in Event History; incomplete ones retry.

Parallel tools are table stakes. Parallel tools with crash semantics you can explain are the design problem. Fair comparison is how you stop lying to yourself about which layer is helping.

https://github.com/ryanlingo/durable-research-agent
