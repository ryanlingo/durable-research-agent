# Feature → Benefit → Outcome

Messaging ladder for this project. Use it for posts, diagrams captions, demos, README blurbs, and talk scripts.

| Layer | Question | Job |
|-------|----------|-----|
| **Feature** | What does this do? | Name the capability or mechanism in plain product language |
| **Benefit** | How does this help the user in a concrete way? | Immediate, specific help (time, cost, risk, toil) |
| **Outcome** | What bigger result does the user want? | The life/work result they actually care about |

Rules:

1. Do not stop at Feature. A diagram or paragraph that only names primitives is unfinished.
2. Benefit must be concrete. Prefer “you do not re-pay completed LLM calls after a Worker dies” over “more reliable.”
3. Outcome is the user’s world, not Temporal’s product pitch. Examples: ship agents that survive production; sleep through deploys; explain a failure without a log archaeology project.
4. Order in prose: lead with Outcome or Benefit when persuading; use Feature when teaching mechanics. Always be able to state all three.
5. Temporal terms stay glossary-correct (`temporal-concepts.md`). FBO wraps them; it does not replace them.

---

## Ladder for this lab

### Side-by-side research agent

| Layer | Copy |
|-------|------|
| Feature | Same multi-step research agent twice: asyncio + checkpoints vs Temporal Workflow Execution + Activities |
| Benefit | You can crash both mid-run and see token waste, lost work, and resume behavior on one screen |
| Outcome | You can teach (or decide) whether durable control flow belongs in your agent stack with evidence, not slides |

### Durable Execution

| Layer | Copy |
|-------|------|
| Feature | Durable Execution: a Workflow Execution maintains state and progress through failures via Event History |
| Benefit | When a Worker Process dies, completed Activities are not re-executed on Event History replay |
| Outcome | Long-running agent work survives restarts and deploys without becoming a paid re-run lottery |

### Activity

| Layer | Copy |
|-------|------|
| Feature | A single well-defined unit of work (LLM, search, evaluate) whose result is recorded in Event History |
| Benefit | Boundaries for retries, timeouts, and “what already finished” after a crash |
| Outcome | You pay for model and tool work once per success, not once per pod death |

### Event History

| Layer | Copy |
|-------|------|
| Feature | Append-only log of Events for a Workflow Execution |
| Benefit | One place to see what happened and what will be reused on resume |
| Outcome | Debug and postmortem without reconstructing the run from scattered logs |

### Signal

| Layer | Copy |
|-------|------|
| Feature | Asynchronous request to a Workflow Execution |
| Benefit | Human approval does not need a live process polling a database |
| Outcome | People can review agent output on human time without keeping workers warm |

### Query

| Layer | Copy |
|-------|------|
| Feature | Synchronous read of Workflow Execution state |
| Benefit | UIs and operators can ask “where is this run?” without changing business state |
| Outcome | Observability that matches how the execution actually progresses |

### Experiment UI (Showcase)

| Layer | Copy |
|-------|------|
| Feature | Dual-column scripted crash with token comparison |
| Benefit | You can show the story without API keys or a Temporal Service |
| Outcome | A room understands the reliability gap in under two minutes |

---

## Checklist before publishing

- [ ] Feature named accurately (Temporal glossary if applicable)
- [ ] Benefit is concrete (who, when, what changes in their day)
- [ ] Outcome is the bigger result, not a restatement of the benefit
- [ ] No layer skipped for “obvious” product audience
- [ ] Caption or opening line does not end on Feature alone
