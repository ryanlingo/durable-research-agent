# Temporal overview

Temporal is a scalable and reliable runtime for reentrant processes called Temporal Workflow Executions. The Temporal Platform is a Temporal Service plus Worker Processes.

## Durable Execution

Durable Execution means a Workflow Execution can maintain its state and progress through failures, crashes, or outages. Progress is recorded as Events in an Event History. Recovery works by replaying that history so Workflow code returns to the same logical state. Completed Activity results are reused from history rather than re-invoking the Activity.

## Workflow and Activity

A Workflow Definition is code that orchestrates steps. A Workflow Execution is a running instance of that definition. Workflow code must be deterministic: given the same Event History, it must make the same decisions.

An Activity is a function that performs a single well-defined action and may be non-deterministic. LLM calls, database access, and external APIs belong in Activities. When an Activity completes, its result is recorded in Event History.

## Worker Process and Task Queue

A Worker Process polls a Task Queue, runs Workflow and Activity code, and reports results to the Temporal Service. If a Worker Process dies, another Worker can continue the same Workflow Execution by replaying Event History.

## Signal and Query

A Signal is an asynchronous request to a Workflow Execution (for example human approval). A Query is a synchronous read of Workflow Execution state. Signals change what the Workflow can observe; Queries report state without advancing business logic as a Signal would.

## Event History

Event History is an append-only log of Events for a Workflow Execution. It is the source of truth for what already happened and the foundation of Durable Execution. Application print statements are not Event History.

## Retry Policy

A Retry Policy tells the Temporal Service how to retry failed Workflow or Activity Task Executions. Retries are configured on the platform path, not only inside ad hoc application loops.
