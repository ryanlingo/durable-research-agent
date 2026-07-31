# Reliability problems in AI agents

Most agent frameworks treat the process as ephemeral. If the process dies mid-run:

- Intermediate tool results are lost
- Expensive LLM calls are re-executed
- Human-in-the-loop state must be reconstructed from external storage
- Debugging requires correlating application logs across systems

Production agents need durable control flow, not only durable tool calls. State must survive process restarts, deployments, and network partitions.

With Temporal, that durability is defined for a Workflow Execution: Durable Execution means the run can keep state and progress through failures. Progress is recorded in Event History. A Worker can die; another Worker can continue the same execution by replaying history. Completed Activity results are reused from history rather than re-run.
