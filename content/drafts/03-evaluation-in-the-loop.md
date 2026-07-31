---
title: Evaluation belongs inside the agent control flow
status: outline
series: durable-agents
post: 3
style: context/STYLE.md
estimated_read: 6 min
---

# Evaluation belongs inside the agent control flow

Offline judges and red-team notebooks arrive after the bad report has already left the building. This lab puts evaluation on the path the tokens already walk: write a draft, score faithfulness and relevance against retrieved context, refine once if the overall score is below 0.7, then ask a human. Same judge prompt on both stacks. The point is not inventing eval. It is treating judge and refine as control-flow work with cost, retries, and crash semantics (Activities on the Temporal path).

## What to write up (after one live scored run)

Open with a fluent draft that is weakly grounded so “reads well” is visibly not “faithful.”

Describe the two scores and the gate. Faithfulness asks whether claims are supported by context. Relevance asks whether the report answers the query. Overall is their average; the threshold is 0.7. Show the JSON the judge returns from a real run, not a fabricated sample.

Cap refine at one attempt. That bounds cost and still proves the loop. Infinite refine thrash is a different bug.

Tie crash behavior to post 1. Crash after draft and before eval: what re-runs? Crash after a failed eval during refine: what is preserved? Temporal’s Activity boundaries make write and evaluate separate units in Event History; the checkpoint path only does as well as the fields you saved.

Keep human approval after the machine judge. Machines catch grounding failures. Humans catch taste, policy, and brand. Do not spend reviewer time on unfaithful drafts.

## Still needed before draft → ready

- One real evaluation JSON from a live run
- Token cost of judge vs writer for a small comparison
- Full prose for the sections above without a “key takeaways” block

If evaluation only lives in CI notebooks, production will keep inventing ways to skip it.
