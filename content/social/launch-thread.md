---
title: Launch thread and LinkedIn
status: draft
source: drafts/01-not-durable-with-checkpoints.md
style: context/STYLE.md
---

# X thread

1/ I built the same AI research agent twice (asyncio + retries + SQLite checkpoints, and Temporal), then killed both mid-write.

The difference is the curriculum.

2/ Both do: clarify → plan → RAG → parallel search → write → LLM judge → human approval.

Same tools, prompts, and token accounting. Only orchestration changes.

3/ The non-Temporal side has tenacity retries, checkpoints after major steps, and an approval table.

It still loses work when the process dies mid-LLM call.

4/ After restart: in-flight draft gone, recovery incomplete by default, tokens often paid again for steps you thought you saved.

5/ Temporal: the Worker can die; the Workflow Execution does not. Completed Activities stay completed. Event History is the record of what happened.

6/ If a crash doubles your token bill, your control plane is incomplete.

7/ Dual-column experiment UI in the repo. Showcase mode needs no API keys.

8/ Retries ≠ durability. Checkpoints ≠ durable execution.

[repo link]

---

# LinkedIn

Most production AI agents are one pod restart away from losing the expensive middle of a run.

I implemented the same multi-step research agent twice: asyncio + tenacity + SQLite checkpoints + polling approval, and Temporal (Workflow, Activities, Signals). Same RAG, tools, judge prompt, and token counters. Then I crash both mid-write.

The non-Temporal path still does the responsible things. Recovery is still partial. In-flight LLM work is still gone. The token bill still climbs.

The Temporal path resumes by replaying Event History. Completed Activities are not re-run. Human approval is a Signal, not a live polling process.

The metric that travels: tokens after crash-and-restart.

Lab and dual-pipeline UI are in the repo, including a Showcase mode built for screen recordings.

Which crash point would you instrument first in your own agent: write, tool batch, or approval wait?
