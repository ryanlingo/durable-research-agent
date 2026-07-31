# Durable Research Agent

A side-by-side lab: the **same** multi-step research agent on a typical production stack and on Temporal.

**Feature:** dual implementations that share tools, RAG, evaluation, and token accounting.  
**Benefit:** crash both mid-run and compare lost work, re-execution, and token cost.  
**Outcome:** decide—with evidence—whether durable control flow belongs in your agent architecture.

| After a crash mid-write | Typical stack (`without_temporal/`) | Temporal (`with_temporal/`) |
|---|---|---|
| In-flight LLM result | Lost | Incomplete Activity retries per Retry Policy; completed result is in Event History |
| Work already finished | Often re-run (incomplete recovery) | Completed Activities are not re-executed on replay |
| Token bill | Climbs on restart | Tracks completed Activity work, not worker restarts |
| Human approval | Live process polls SQLite | Signal into the Workflow Execution |
| Observability | Application logs + DB rows | Event History (Temporal Web UI) |

Pipeline (identical on both sides): clarify → plan → RAG → parallel search → write → evaluate → optional refine → human approval.

```
        ┌──────────────────────────────┐
        │  Shared agent logic          │
        │  LLM · RAG · search · eval   │
        └──────────────┬───────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   without_temporal            with_temporal
   asyncio · tenacity          Workflow Execution
   SQLite checkpoints          Activities · Signals · Queries
```

Architecture diagram: [`content/assets/diagrams/02-shared-brain-two-runtimes.svg`](content/assets/diagrams/02-shared-brain-two-runtimes.svg)

Temporal terms follow the [Temporal glossary](https://docs.temporal.io/glossary). Lab vocabulary: [`content/concepts/temporal-concepts.md`](content/concepts/temporal-concepts.md).

---

## Requirements

- Python 3.10+
- [Temporal CLI](https://docs.temporal.io/cli) (for the Temporal path and Web UI)
- OpenAI API key (live agents; Showcase UI does not need one)

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # set OPENAI_API_KEY for live runs
```

### Experiment UI (recommended first look)

```bash
python -m ui.app
# http://127.0.0.1:8765
```

| Mode | Purpose |
|------|---------|
| **Showcase** | Scripted dual crash and token comparison. No API keys or Temporal Service. |
| **Live** | Real agents. Crash/resume non-Temporal from the UI. Temporal needs a Worker and `temporal server start-dev`. |

### Non-Temporal CLI

```bash
python -m without_temporal.run "How does durable execution help AI agents?" --auto-approve
```

Human approval (omit `--auto-approve`):

```bash
python -m without_temporal.approve <RUN_ID> approved
```

### Temporal CLI

```bash
# terminal 1
temporal server start-dev

# terminal 2
python -m with_temporal.worker

# terminal 3
python -m with_temporal.run "How does durable execution help AI agents?" --auto-approve --wait
```

Approval Signal:

```bash
python -m with_temporal.signal_approval <WORKFLOW_ID> approved
```

Temporal Web UI: [http://localhost:8233](http://localhost:8233)

---

## Configuration

Copy [`.env.example`](.env.example) to `.env` (gitignored):

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | — | Required for live LLM and embedding calls |
| `LLM_MODEL` | `gpt-5.6-luna` | Chat/completions model |
| `EMBEDDING_MODEL` | `small` | Resolves to `text-embedding-3-small` |
| `TAVILY_API_KEY` | unset | Optional real web search; otherwise mock search |

---

## Crash recovery

Use the same query; kill both systems at the same point. Walkthrough: [`demos/crash_demo.md`](demos/crash_demo.md).

- **Without Temporal:** resume with `--run-id`. Expect partial recovery and re-paid work.
- **With Temporal:** restart the Worker. The Workflow Execution continues; completed Activities are not re-run when history is replayed.

---

## Repository layout

```text
shared/                 # RAG, evaluation, tools, types, config
without_temporal/       # asyncio + tenacity + SQLite + polling approval
with_temporal/          # Workflow, Activities, Signals, Queries, Worker
ui/                     # Experiment dashboard (FastAPI + static UI)
data/docs/              # Fixed markdown corpus for RAG
demos/                  # Crash recovery procedure
content/                # Teaching assets (see below)
.env.example            # Configuration template
pyproject.toml          # Package metadata and dependencies
requirements.txt        # Pip-friendly install list
```

### Teaching assets (`content/`)

| Path | Contents |
|------|----------|
| `content/concepts/` | Temporal vocabulary, Feature → Benefit → Outcome |
| `content/drafts/` | Long-form posts |
| `content/tutorials/` | Step-by-step how-tos |
| `content/decks/` | Slide decks and outlines |
| `content/assets/diagrams/` | Infographics (SVG + PNG) |
| `content/assets/media/` | Screenshots and recordings |
| `content/social/` | Short-form distribution cuts |

---

## Design principles

1. **Fair comparison** — the non-Temporal path has retries, checkpoints, and approval; it is not a strawman.
2. **Shared brain** — prompts, tools, corpus, judge, and token accounting are identical.
3. **Stable demos** — fixed local RAG corpus; optional Tavily; Showcase mode without cloud.
4. **Docs-aligned Temporal language** - canonical terms first (Workflow Execution, Activity, Event History, Signal, Query, Worker); plain reuse after.
5. **Evaluation in the loop** — faithfulness and relevance gate refinement before human approval.

---

## License

[MIT](LICENSE)
