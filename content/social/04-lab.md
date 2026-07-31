---
title: Post 04 social cuts: side-by-side lab
status: ready
source: drafts/04-side-by-side-lab.md
style: context/STYLE.md
repo: https://github.com/ryanlingo/durable-research-agent
media:
  - ../assets/diagrams/02-shared-brain-two-runtimes.svg
  - ../assets/media/2026-07-31-showcase-mid-run.png
---

# How to post

1. Attach shared-brain diagram or Showcase mid-run screenshot.
2. X as a short thread; LinkedIn as one post.
3. Link the repo once.

---

# X thread

1/ A Temporal-only demo lets skeptics assume the other side was weak on purpose. An asyncio-only demo never shows what Durable Execution changes.

2/ Lab rule: one agent brain, two nervous systems. Shared tools, prompts, RAG, judge, token counters. Only orchestration differs.

3/ Fairness means real checkpoints and parallel search on the non-Temporal path, not a strawman for-loop.

4/ Dual-column UI: Showcase needs no keys. Live needs a Worker and an API key. Crash both mid-write and read the savings panel.

5/ You do not need this research agent. You need one multi-step path you already run, a second implementation that only changes durability, and a crash everyone can see.

Lab: https://github.com/ryanlingo/durable-research-agent

---

# LinkedIn

A Temporal-only demo lets skeptics assume the other side was weak on purpose. An asyncio-only demo never shows what Durable Execution changes.

I built one multi-step research agent and ran it on two stacks: typical production shape (asyncio, tenacity, SQLite, polling approval) and Temporal (Workflow Execution, Activities, Signals). Shared tools, prompts, fixed RAG corpus, judge, and token accounting. Only the control plane changes.

Fair comparison is a design rule: same parallel search, same human gate, same crash point when you measure. The experiment UI makes that visible without a walkthrough call. Showcase mode needs no API keys.

If cloning a second orchestration feels like too much work, that is evidence about the recovery surface area already hidden in the first.

https://github.com/ryanlingo/durable-research-agent

Attach: architecture diagram or dual-pipeline UI screenshot.
