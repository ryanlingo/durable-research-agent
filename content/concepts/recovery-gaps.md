# Intentional recovery gaps (non-Temporal path)

This lab keeps the typical stack **fair but incomplete**. The non-Temporal agent has retries, stage checkpoints, resume by `run_id`, and human approval. It does **not** silently grow into a second workflow engine. The gaps below are curriculum, not accidental omissions.

| Layer | Copy |
|-------|------|
| **Feature** | Documented incomplete resume on `without_temporal` (status gates, post-step checkpoints, re-eval) |
| **Benefit** | After a crash you can name what was lost and what was re-paid without claiming checkpoints equal Durable Execution |
| **Outcome** | You can judge whether multi-step agents need platform-level Event History, not just more SQLite rows |

Canonical Temporal contrast: completed **Activities** are not re-executed on **Event History** replay. See [`temporal-concepts.md`](temporal-concepts.md).

Code entry point: `without_temporal/agent.py` (module docstring + gap markers). UI surfaces re-pays as `re_executed` events and the comparison “What re-ran” list.

---

## Gap catalog

### 1. In-flight write is not a checkpoint unit

**Where:** write path checkpoints at `drafted` only after `_write_report` returns.

**What fails:** process death mid-LLM call. Provider may already bill tokens. SQLite has no draft. Resume rewrites.

**Temporal contrast:** incomplete `write_activity` retries per policy; completed earlier Activities stay done.

**See it:** Showcase **Crash at: writing**, or Live crash during writing then Resume.

### 2. Parallel search is all-or-nothing

**Where:** `asyncio.gather` over plan queries; `searched` checkpoint after the whole batch.

**What fails:** kill mid-gather. Partial returns in the dead process are gone. Resume re-runs the plan.

**Temporal contrast:** each `search_activity` is its own Activity. Finished searches remain in Event History.

**See it:** Showcase **Crash at: searching**. Series post 05: `drafts/05-parallel-tools-fair-comparison.md`.

### 3. Coarse status gates, not field-level resume

**Where:** `if state.status in (...)` decides whether to clarify, plan, or search again.

**What fails:** status and payload can disagree (empty plan with `planned`, partial hydrate). Recovery is string-matching, not a durable command log.

**Temporal contrast:** Workflow code plus Event History define progress; you do not maintain a parallel skip table by hand for every field.

### 4. Evaluation short-circuit is incomplete

**Where:** after resume, the write/eval loop may re-run `evaluate_report` even when an evaluation was loaded from the checkpoint (tracked as re-ran `evaluating`).

**What fails:** judge tokens paid twice after some crash points (e.g. resume during approval wait).

**Temporal contrast:** a completed evaluate Activity is not re-executed on replay.

**See it:** recovery tests in `tests/test_recovery_tracking.py`.

### 5. Manual nested reconstruction

**Where:** resume builds `SearchResult`, `RetrievedChunk`, `EvaluationResult` from dicts.

**What fails:** schema drift, missing nested token fields, silent defaults. Every new state field needs more resume code.

**Temporal contrast:** Activity results are recorded by the platform; replay restores them without app-level ORM for every crash.

### 6. Token ledger vs provider bill

**Where:** `total_tokens` only advances when a call returns and the agent adds usage. In-flight death is invisible to SQLite. `re_executed` records re-pays after resume, not the lost partial bill.

**What fails:** “tokens so far” understates true spend until rewrite shows up on the bill.

**Temporal contrast:** completed Activity costs stay associated with completed work; restarts do not double-count finished Activities.

---

## What we deliberately do keep fair

- Same tools, prompts, corpus, judge, and token counters as Temporal  
- Real retries (tenacity) and real stage checkpoints  
- Parallel search (not sequential “to make Temporal look good”)  
- Human approval path (polling), not “auto only”  

Closing every gap above inside `without_temporal` would mean building durable per-step journals, idempotency keys, and resume graphs. That is the argument for a Workflow Execution, not a weekend of extra SQLite columns.

---

## Related

- Crash procedure: [`../../demos/crash_demo.md`](../../demos/crash_demo.md)  
- Post 01 (crash/checkpoints): [`../drafts/01-not-durable-with-checkpoints.md`](../drafts/01-not-durable-with-checkpoints.md)  
- Post 05 (parallel tools): [`../drafts/05-parallel-tools-fair-comparison.md`](../drafts/05-parallel-tools-fair-comparison.md)  
- Lab write-up: [`../drafts/recovery-gaps-on-purpose.md`](../drafts/recovery-gaps-on-purpose.md)  
