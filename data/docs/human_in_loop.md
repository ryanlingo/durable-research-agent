# Human-in-the-loop patterns

Long-running agents often need human input for clarification or approval. Naive implementations poll a database or message queue from a live process. Problems include race conditions, lost updates, and idle compute while waiting.

Ideal behavior: control flow pauses, records that it is waiting, does not require a dedicated polling process, and resumes when the human responds. The reason for the pause should remain inspectable later.

In Temporal, a Signal is an asynchronous request to a Workflow Execution (for example approval). A Query is a synchronous read of that run’s state. Waiting for a Signal does not require application-level polling of a database row. Event History records that the run waited and what arrived.
