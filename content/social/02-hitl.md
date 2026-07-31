---
title: Post 02 social cuts: human-in-the-loop
status: ready
source: drafts/02-hitl-without-polling.md
style: context/STYLE.md
repo: https://github.com/ryanlingo/durable-research-agent
media:
  - ../assets/diagrams/05-hitl-polling-vs-signal.svg
---

# How to post

1. Attach poll-vs-Signal diagram if the platform allows images.
2. X as a short thread; LinkedIn as one post.
3. Link the repo once.

---

# X thread

1/ If approval requires a Python process to stay alive and poll a database, you do not have durable human-in-the-loop. You have a long-lived poller that sometimes calls a model.

2/ Non-Temporal path in the lab: write pending to SQLite, sleep 2s, read again. Fine on a laptop. Awkward for multi-day review, deploys, and scale-to-zero.

3/ Temporal path: Workflow Execution waits for a Signal. No application poll loop. Worker need not stay warm for human time.

4/ Agents stretch time: clarification, compliance, "ship the draft tomorrow." Each wait charges you if the process must stay scheduled.

5/ Same research agent, two stacks. Post 1 was crash recovery. This one is the approval gate.

Lab: https://github.com/ryanlingo/durable-research-agent

---

# LinkedIn

If approval requires a process to stay up and poll a row every two seconds, you do not have durable human-in-the-loop. You have a long-lived poller.

In a side-by-side lab I run the same multi-step research agent twice. After evaluation, the typical stack writes `pending` to SQLite and loops. The Temporal path waits for a Signal into the Workflow Execution. No application poll loop, and the Worker does not need to stay scheduled while a human thinks.

Agent systems stretch time on purpose: clarification, second looks, compliance. Polling processes charge you for human delay. Signals do not.

Same tools and prompts as the crash-recovery post. Only the control plane changes.

https://github.com/ryanlingo/durable-research-agent

Attach: poll vs Signal diagram (`content/assets/diagrams/05-hitl-polling-vs-signal.svg`).
