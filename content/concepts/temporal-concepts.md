# Temporal concepts (docs-aligned)

Canonical definitions for this project. Prefer these terms in drafts, diagrams, demos, UI copy, and the RAG corpus.

Source of truth: [Temporal Glossary](https://docs.temporal.io/glossary) and linked concept pages. When wording here and docs diverge, **docs win**. Update this file after checking the glossary.

Capitalization: use Temporal’s product capitalization in formal prose (**Workflow Execution**, **Activity**, **Event History**, **Task Queue**, **Worker Process**, **Signal**, **Query**). Informal speech can say “the workflow” once the term is introduced.

---

## Core platform

### Temporal

A scalable and reliable runtime for reentrant processes called Temporal Workflow Executions.

Docs: [What is Temporal?](https://docs.temporal.io/temporal)

### Temporal Platform

A Temporal Service plus Worker Processes.

### Temporal Service

A Temporal Server paired with Persistence and Visibility stores. Prefer this term over the older “Temporal Cluster.”

### Temporal Client

SDK APIs that communicate with a Temporal Service (start Workflow Executions, send Signals, issue Queries, etc.).

### Temporal Web UI

UI that shows Workflow Execution state and metadata for debugging. Local dev default: `http://localhost:8233`.

---

## Durable Execution

**Durable Execution** (Temporal context): the ability of a **Workflow Execution** to maintain its state and progress even in the face of failures, crashes, or server outages.

Docs: [Glossary: Durable Execution](https://docs.temporal.io/glossary#durable-execution)

How recovery works (for teaching): the Temporal Service appends **Events** to an **Event History**. When work resumes, a Worker can **replay** that history so Workflow code returns to the same logical state without re-executing completed **Activities**. Do not describe this as “restoring RAM.” Prefer: replay of Event History.

---

## Workflow

In conversation, “Workflow” may mean Definition, Type, or Execution. Be explicit when precision matters.

| Term | Meaning |
|------|---------|
| **Workflow Definition** | Code that defines the constraints of a Workflow Execution |
| **Workflow Type** | Name that maps to a Workflow Definition |
| **Workflow Execution** | Running instance: durable, scalable, reliable, reactive function execution; main unit of a Temporal Application |

Docs: [Workflows](https://docs.temporal.io/workflows), [Workflow Execution](https://docs.temporal.io/workflow-execution)

### Determinism

Workflow code must make the same decisions given the same history (deterministic). Non-deterministic work (network, LLM, clock entropy used incorrectly) belongs in Activities or other Temporal primitives (Timers, Side Effects) as documented.

In this lab: `ResearchWorkflow` is the Workflow Definition; each `research-…` id is a Workflow Execution.

---

## Activity

An **Activity** is a normal function or method that executes a single, well-defined action (short or long). Activity code may be non-deterministic. Docs recommend Activities be **idempotent**.

Examples of work that belongs in Activities: API calls, database access, LLM invocations, file I/O.

When a Workflow schedules an Activity, the result is recorded in Event History. On replay, that recorded result is reused; the Activity function is not re-run for completed work.

| Term | Meaning |
|------|---------|
| **Activity Definition** | Code that defines Activity Task Execution constraints |
| **Activity Type** | Name mapped to an Activity Definition |
| **Activity Execution** | Full chain of Activity Task Executions for that invocation |

Docs: [Activities](https://docs.temporal.io/activities)

In this lab: clarify, plan, retrieve, search, write, and evaluate are Activities.

---

## Worker and Task Queue

### Worker Process

Polls a Task Queue, dequeues Tasks, executes your Workflow/Activity code, and responds to the Temporal Service with results.

### Worker Program

Static code that defines Worker Process constraints (which Workflows and Activities are registered).

### Task Queue

A first-in, first-out queue that a Worker Process polls for Tasks.

Docs: [Workers](https://docs.temporal.io/workers), [Task Queue](https://docs.temporal.io/task-queue)

In this lab: Task Queue name is `research-agent-task-queue` (`with_temporal/worker.py`).

---

## Event and Event History

### Event

Created by the Temporal Service in response to external occurrences and Commands from a Workflow Execution.

### Event History

An **append-only log of Events** that represents the full state of a Workflow Execution. It is what makes Durable Execution possible: progress is reconstructed by replaying history, not by hoping process memory survived.

Docs: [Events and Event History](https://docs.temporal.io/workflow-execution/event)

Avoid saying “logs” when you mean Event History. Application print statements are not Event History.

---

## Signals, Queries, Updates

### Signal

An **asynchronous** request to a Workflow Execution. Used to push data in (for example human approval) without polling inside application code.

Docs: [Signals](https://docs.temporal.io/sending-messages#sending-signals)

In this lab: `submit_approval`, `submit_clarification`.

### Query

A **synchronous** operation used to **report the state** of a Workflow Execution (read-only handler; does not change Workflow state).

Docs: [Queries](https://docs.temporal.io/sending-messages#sending-queries)

In this lab: `status` Query on `ResearchWorkflow`.

### Update

A request to and a response from a Workflow Execution (request/response messaging). Not used in this lab yet; do not invent Update behavior in diagrams.

Docs: [Updates](https://docs.temporal.io/sending-messages#sending-updates)

---

## Retry Policy

A collection of attributes that instructs the Temporal Service how to retry a failure of a Workflow Execution or an Activity Task Execution.

Docs: [Retry Policies](https://docs.temporal.io/encyclopedia/retry-policies)

In this lab: Activities use a Retry Policy with a maximum attempt count (see `with_temporal/workflows.py`). This is not the same as tenacity retries in the non-Temporal path.

---

## Identifiers

| Term | Meaning |
|------|---------|
| **Workflow Id** | Application-level id for a Workflow Execution; unique among Open executions in a Namespace |
| **Run Id** | Globally unique platform-level id for a Workflow Execution |
| **Namespace** | Unit of isolation within the Temporal Platform |

---

## Phrasing rules for this repo

1. First mention: use the glossary term (**Workflow Execution**, **Activity**, **Event History**, **Worker Process**, **Signal**, **Query**, **Task Queue**). After that, reuse plain words (*run*, *step*, *history*, *worker*) when the meaning is clear.
2. Do not confuse **Event History** with application logs.
3. A **Worker Process** can die while the **Workflow Execution** continues. Say that clearly on first mention.
4. Completed **Activities** are not re-executed on replay; do not claim magical exactly-once external side effects unless you also discuss Activity idempotency.
5. **Signal** = async inbound; **Query** = sync state read. You may say “approval arrived” after Signal is established.
6. Prefer **Temporal Service** over “cluster” in formal copy; informal “the service” is fine after.
7. Paraphrase glossary definitions; do not invent a parallel product jargon (for example a home-grown “durable step” brand).
---

## How this lab maps

| Lab piece | Temporal concept |
|-----------|------------------|
| `ResearchWorkflow` | Workflow Definition / Type |
| `python -m with_temporal.run …` | Starts a Workflow Execution (Temporal Client) |
| `python -m with_temporal.worker` | Worker Program / Worker Process |
| `research-agent-task-queue` | Task Queue |
| `*_activity` functions | Activity Definitions |
| `submit_approval` / `submit_clarification` | Signals |
| `status` | Query |
| UI at `:8233` | Temporal Web UI (Event History, etc.) |
| Crash Worker, restart Worker | Durable Execution via Event History replay |
