---
title: Human-in-the-loop should not require a live process
status: draft
series: durable-agents
post: 2
style: context/STYLE.md
estimated_read: 6 min
---

# Human-in-the-loop should not require a live process

If approval requires a Python process to stay alive and poll a database, you do not have durable human-in-the-loop. You have a long-lived poller that sometimes calls a model.

Agent demos treat “wait for a human” as a checkbox. Production treats it as wall-clock time that can last minutes or days. The wait is part of the architecture. Implementing it as `sleep` and a SELECT loop pushes cost and fragility onto human latency instead of model latency.

## How the two stacks wait

After evaluation, the non-Temporal agent writes `approval_status = pending`, prints a command for another terminal, and loops: read the row, sleep two seconds, repeat. That is fine on a laptop. In production it means a worker stays scheduled for the whole wait, deploys and scale-to-zero fight you, and a crash during the wait sends you back into recovery code. The workflow is “a process that has not exited yet.”

The Temporal Workflow Execution reaches approval and waits for a Signal: an asynchronous request into that run. No application poll loop, and the same worker does not need to stay alive. When a human or another service signals approval, the run continues from history. A Query can report that it is waiting without changing business state.

## Why this shows up in agents

LLM systems stretch time with clarification, second looks at tool output, compliance review, and “ship the draft tomorrow.” Each is a wait. Polling processes charge you for human delay. Durable waits do not.

The SQLite approval table is a reasonable first cut. Many teams ship it. The failure mode is not that polling is immoral. It is that multi-day review, restarts, and inspectable history become your problem again, in application code, every time.

| Concern | Polling process | Signal |
|---|---|---|
| Compute while waiting | Process stays up and wakes | Workflow waits without a poll loop |
| Worker restart mid-wait | Rehydrate and re-enter the loop | Built into Durable Execution |
| What you can inspect later | Whatever you logged or stored | Signal shows up in Event History |
| Multi-day approval | Awkward | Natural |

## Demo

Without Temporal, omit `--auto-approve`, leave the process in the poll loop, then run `python -m without_temporal.approve <RUN_ID> approved`.

With Temporal, omit `--auto-approve`, optionally stop the worker, then run `python -m with_temporal.signal_approval <WORKFLOW_ID> approved`. History should show completed Activities, a wait, a Signal, then completion.
If a person must touch the run, design the wait the way you design the tool call: durable, observable, and restart-safe.
