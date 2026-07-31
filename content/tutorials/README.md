# Tutorials

Step-by-step how-tos a reader can follow without a call.

## Put here

- Crash recovery walkthroughs (CLI and UI)
- Temporal path: Service, Worker Process, start Workflow Execution, Signal, Query
- Non-Temporal path: run, approve, resume with `run_id`
- Experiment UI: Showcase vs Live

## Naming

```
NN-short-slug.md
```

Numbered for a recommended order. Example: `01-showcase-ui.md`, `02-crash-without-temporal.md`, `03-crash-with-temporal.md`.

## Rules

- Prefer commands that match the root `README.md` and `demos/`
- Link diagrams from [`../assets/diagrams/`](../assets/diagrams/) instead of describing layout only in prose
- Temporal vocabulary must match [`../concepts/temporal-concepts.md`](../concepts/temporal-concepts.md)
- Each tutorial should state Feature / Benefit / Outcome once at the top (see FBO doc)

## Related

- Short crash script: [`../../demos/crash_demo.md`](../../demos/crash_demo.md)
- Loom shot list: [`../assets/loom-crash-demo.md`](../assets/loom-crash-demo.md)
