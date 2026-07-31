---
title: Post 03 social cuts: evaluation in the loop
status: ready
source: drafts/03-evaluation-in-the-loop.md
style: context/STYLE.md
repo: https://github.com/ryanlingo/durable-research-agent
---

# How to post

1. Optional: paste the sample eval JSON from the draft.
2. X as a short thread; LinkedIn as one post.
3. Link the repo once.

---

# X thread

1/ Offline judges and red-team notebooks arrive after the bad report has already left the building.

2/ Production agents need the judge on the path the tokens already walk: write, evaluate, refine once if overall is below 0.7, then human approval.

3/ Same judge prompt on asyncio and Temporal in this lab. Faithfulness + relevance, average, pass at 0.7.

4/ Live sample from the lab: faithfulness 0.98, relevance 1.0, overall 0.99. A pass. Failures trigger one rewrite, then the gate again.

5/ Evaluation is control-flow work with cost, retries, and crash semantics. Not a side script.

Lab: https://github.com/ryanlingo/durable-research-agent

---

# LinkedIn

Offline judges arrive after the bad report has already left the building. Production agents need the judge on the path the tokens already walk.

In this lab both stacks run the same LLM-as-judge after draft: faithfulness and relevance from 0.0 to 1.0, overall as the average, pass threshold 0.7. Fail once and you refine once. Cap refine so cost stays bounded.

On Temporal, evaluation is an Activity. On the non-Temporal path it is a function call with a checkpoint when status becomes evaluated. Same prompt. The point is not inventing eval. It is treating judge and refine as steps with crash and cost semantics, then human approval after the machine gate.

Sample from a live lab run: overall 0.99 with grounded reasoning. Reviewers should not be the first filter for unfaithful prose.

https://github.com/ryanlingo/durable-research-agent
