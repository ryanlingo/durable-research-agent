# Crash recovery demonstration

Use the same query in both systems and kill the process at the same point.

Longer walkthroughs: [Showcase UI](../content/tutorials/01-showcase-ui.md) · [non-Temporal CLI](../content/tutorials/02-crash-without-temporal.md) · [Temporal Worker](../content/tutorials/03-crash-with-temporal.md) · [Live mode](../content/tutorials/04-live-mode.md).

Timed talk / interview: [interview-playbook.md](interview-playbook.md).

## Shared query

```
How does durable execution help AI agents survive process crashes?
```

## Without Temporal

```bash
# Terminal 1
python -m without_temporal.run "How does durable execution help AI agents survive process crashes?" --auto-approve

# After you see "checkpointed at 'planned'" or "checkpointed at 'searched'":
# Terminal 2 – kill the process
pkill -f "without_temporal.run"

# Restart with the same run-id (printed at start)
python -m without_temporal.run --run-id <RUN_ID> --auto-approve
```

Observe:
- Which intermediate results were lost
- Whether LLM / search calls are re-executed (token waste)
- How complete the recovery logic actually is

Intentional gaps (mid-write, mid-gather, re-eval, coarse status) are catalogued in
[`content/concepts/recovery-gaps.md`](../content/concepts/recovery-gaps.md).
Do not “fix” them without updating that doc; they are the comparison curriculum.

## With Temporal

```bash
# Terminal 1 – start worker
python -m with_temporal.worker

# Terminal 2 – start workflow
python -m with_temporal.run "How does durable execution help AI agents survive process crashes?" --auto-approve --wait

# After the worker has completed planning / searching (watch Temporal UI):
# Terminal 3 – kill the worker
pkill -f "with_temporal.worker"

# Restart the worker
python -m with_temporal.worker
```

Observe:
- The Workflow Execution continues after the Worker restarts
- Completed Activities are not re-executed when history is replayed
- Event History is visible in the Temporal Web UI (http://localhost:8233)
- Human approval (if not auto) is a Signal into the run

## Human-in-the-loop comparison

Without Temporal: poll a database row every 2 seconds.

With Temporal:
```bash
# while workflow is in awaiting_approval
python -m with_temporal.signal_approval <WORKFLOW_ID> approved
```
