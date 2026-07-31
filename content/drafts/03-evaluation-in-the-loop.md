---
title: Evaluation belongs inside the agent control flow
status: ready
series: durable-agents
post: 3
style: context/STYLE.md
estimated_read: 6 min
repo: https://github.com/ryanlingo/durable-research-agent
---

# Evaluation belongs inside the agent control flow

Offline judges and red-team notebooks arrive after the bad report has already left the building. Production agents need the judge on the path the tokens already walk.

You want fewer fluent but ungrounded reports reaching a human reviewer. The concrete help is a gate that scores the draft before approval. The feature is LLM-as-judge inside both stacks of this lab: write, evaluate, refine once if the overall score is below 0.7, then human approval. Same judge prompt on asyncio and Temporal. The point is not inventing eval. It is treating judge and refine as control-flow work with cost, retries, and crash semantics.

## What the judge scores

Two dimensions from 0.0 to 1.0:

| Score | Question |
|-------|----------|
| **Faithfulness** | Is every factual claim supported by retrieved context? |
| **Relevance** | Does the report answer the query? |
| **Overall** | Average of the two. Pass threshold: **0.7** |

Fluent prose can fail faithfulness. A tight answer to the wrong question fails relevance. Reviewers should not be the first filter for either.

From a live run of this lab (`How does durable execution help AI agents?`):

```json
{
  "faithfulness": 0.98,
  "relevance": 1.0,
  "overall": 0.99,
  "reasoning": "The report directly answers how durable execution benefits AI agents and closely reflects the retrieved context, covering state persistence, recovery after failures, avoiding repeated LLM calls, long-running tasks, human-in-the-loop, evaluation, and durable control flow."
}
```

That is a pass. A failing overall triggers one rewrite, then the gate runs again. Cap refine at one attempt. That bounds cost and still proves the loop. Infinite refine thrash is a different bug.

## Same judge, two orchestrations

Both implementations call the same `evaluate_report` helper in `shared/evaluate.py`. On the Temporal path, evaluation is an Activity. Its result is recorded in Event History like any other Activity. On the non-Temporal path, evaluation is a function call after write, with a SQLite checkpoint when status becomes `evaluated`.

| | Without Temporal | With Temporal |
|---|---|---|
| Where eval runs | After draft, in-process | `evaluate_activity` |
| On crash after draft, before eval | Draft may be saved; eval re-runs if not checkpointed cleanly | Incomplete Activity retries; completed write is not re-done if it finished |
| On crash during refine | Easy to lose which attempt you were on | History shows write / eval / refine boundaries |
| Tokens | Judge spend is in the same running total | Same accounting, Activity-scoped |

Crash recovery still matters here. Post 1 showed re-paid work mid-write. Mid-eval is the same class of failure: you either re-run paid judge tokens or you resume from a durable boundary.

## Humans after machines

Order in this lab:

1. Write draft  
2. Machine judge (faithfulness + relevance)  
3. Optional one refine  
4. Human approval  

Machines catch grounding and off-topic drafts. Humans catch taste, policy, and brand. Do not spend reviewer time on unfaithful prose that a cheap gate could reject.

## Seeing it

```bash
python -m without_temporal.run "How does durable execution help AI agents?" --auto-approve
# META prints faithfulness, relevance, overall, and reason

python -m with_temporal.run "How does durable execution help AI agents?" --auto-approve --wait
# result.evaluation carries the same shape
```

Lab: https://github.com/ryanlingo/durable-research-agent  

If evaluation only lives in CI notebooks, production will keep inventing ways to skip it. Put the judge on the path the draft already walks.
