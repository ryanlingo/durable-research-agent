---
title: Durable agents crash lab
status: ready
format: outline (build slides from this; export as pptx/key later)
audience: AI engineers, hiring managers, internal Temporal / platform talks
duration:
  short: 10-12 min
  interview: 20-25 min with live Showcase
repo: https://github.com/ryanlingo/durable-research-agent
style: context/STYLE.md
terms: content/concepts/temporal-concepts.md
fbo: content/concepts/feature-benefit-outcome.md
---

# Durable agents crash lab (deck outline)

**Outcome first:** You can decide whether multi-step AI agents need Durable Execution with evidence (tokens, re-ran work), not slides about reliability.

**Benefit:** Crash the same agent twice and see what is lost, re-paid, and reused.

**Feature:** Side-by-side research agent: asyncio + SQLite checkpoints vs Temporal Workflow Execution + Activities.

Build the deck in your tool of choice. One idea per slide. Prefer diagrams and UI captures already in `content/assets/`. Black and white visual system: `content/assets/diagrams/STYLE.md`.

---

## Slide map (12 slides, short talk)

| # | Title | Time |
|---|--------|------|
| 1 | Title / claim | 0:30 |
| 2 | The failure we care about | 1:00 |
| 3 | Same agent, two stacks | 1:00 |
| 4 | Pipeline (shared brain) | 0:45 |
| 5 | Architecture | 1:00 |
| 6 | Demo: Showcase (live or video) | 3:00 |
| 7 | After the crash: tokens | 1:00 |
| 8 | Without Temporal: what re-ran | 1:00 |
| 9 | With Temporal: Worker vs Execution | 1:00 |
| 10 | HITL: poll vs Signal | 0:45 |
| 11 | Fairness + intentional gaps | 1:00 |
| 12 | How to try it / close | 0:45 |

Interview version: insert live CLI or Live UI after slide 6; expand Q&A after 12.

---

## Slides

### 1. Title

**On slide**

- Durable agents crash lab  
- Same research agent. Two control planes. One kill -9.  
- Repo: github.com/ryanlingo/durable-research-agent  

**Say**

Multi-step agents die when the process dies. Today we measure that with tokens, not slogans.

**Visual:** plain title; optional dual-column idle screenshot  
`content/assets/media/2026-07-31-showcase-idle.png`

---

### 2. The failure we care about

**On slide**

Process dies mid-write (deploy, OOM, laptop sleep).

| Question | Why it matters |
|----------|----------------|
| What is lost? | In-flight LLM result |
| What is re-paid? | Plan, write, judge… |
| What is reused? | Completed work, or not |

**Say**

Retries fix bad HTTP. They do not fix process death. Checkpoints help only as far as the recovery code you maintain.

**Visual:** none required; or pipeline with a red X on “writing” (keep B&W: dashed box on writing)

---

### 3. Same agent, two stacks

**On slide**

| | Typical stack | Temporal |
|--|---------------|----------|
| Control flow | asyncio | Workflow Execution |
| Retries | tenacity | Activity Retry Policy |
| State after crash | SQLite you maintain | Event History |
| Human approval | poll a DB row | Signal |

Shared: tools, prompts, RAG corpus, judge, token counters.

**Say**

Only orchestration changes. If tokens diverge after a crash, that is the control plane, not a different model.

**Visual:** table only

---

### 4. Pipeline (shared brain)

**On slide**

clarify → plan → retrieve → **search (parallel)** → write → evaluate → approve

**Say**

Ordinary agent work. If durability is messy here, it is messier in a larger system. Search is parallel on both sides on purpose (fairness).

**Visual:** `content/assets/diagrams/06-pipeline-linear.svg`

---

### 5. Architecture

**On slide**

Shared agent logic above the split. `without_temporal` left. `with_temporal` right.

**Say**

Everything above the line is the experimental control. Everything below is the product decision when you “just ship an agent.”

**Visual:** `content/assets/diagrams/02-shared-brain-two-runtimes.svg`

---

### 6. Demo: Showcase

**On slide**

- Mode: Showcase (no API keys)  
- Crash at: writing  
- Watch dual pipelines  

**Do (preferred)**

`make demo` or `python -m ui.app` → Run. Pace: Talk.

**Or play**

`content/assets/media/2026-07-31-showcase-crash-demo.mp4`

**Say**

Left: process + checkpoints. Right: Workflow Execution + Activities. Same crash point.

**Visual:** live UI or  
`content/assets/media/2026-07-31-showcase-mid-run.png`

**Speaker tip:** Stop talking while pipelines move. Point at crash, then recovery.

---

### 7. After the crash: tokens

**On slide**

Scripted Showcase (mid-write):

| | Tokens |
|--|--------|
| Without Temporal | ~6,520 |
| With Temporal | ~4,590 |
| Temporal savings | ~1,930 (~29.6%) |

**Say**

Reliability shows up as money. The bill tracks how complete your resume path is.

**Visual:** `content/assets/media/2026-07-31-showcase-comparison-panel.png`

---

### 8. Without Temporal: what re-ran

**On slide**

- In-flight draft not checkpointed → rewrite  
- Incomplete recovery can re-touch earlier steps  
- UI lists **What re-ran** + token deltas  

**Say**

This path is not a strawman. It has retries, checkpoints, and approval. It still re-pays work you thought you saved. Gaps are intentional and catalogued (mid-gather, re-eval, coarse status).

**Visual:** `content/assets/diagrams/03-crash-without-temporal.svg`  
Optional: comparison “What re-ran” crop

**Reference:** `content/concepts/recovery-gaps.md`

---

### 9. With Temporal: Worker vs Execution

**On slide**

- Kill the **Worker Process** ≠ kill the **Workflow Execution**  
- **Event History** records completed **Activities**  
- On resume: replay history; completed Activities not re-executed  

**Say**

Durable Execution means the run keeps progress through failures. You design the agent. You stop re-implementing a half workflow engine beside it.

**Visual:** `content/assets/diagrams/04-crash-with-temporal.svg`  
Optional: `content/assets/media/2026-07-31-temporal-web-ui.png`

---

### 10. HITL: poll vs Signal

**On slide**

| Without | With |
|---------|------|
| Process polls SQLite every 2s | **Signal** into Workflow Execution |
| Process must stay scheduled | Worker need not stay warm for the wait |

**Say**

Human time is long. Polling processes charge you for waiting. Signals do not.

**Visual:** `content/assets/diagrams/05-hitl-polling-vs-signal.svg`

---

### 11. Fairness + intentional gaps

**On slide**

Fair:

- Same tools, parallel search, judge, tokens  
- Real checkpoints and approval on the left  

Intentional gaps (do not “fix” without updating docs):

1. Mid-write draft boundary  
2. Mid-gather search batch  
3. Coarse status resume  
4. Re-eval after some resumes  

**Say**

Closing every gap in-app is how teams invent a private Temporal with worse observability. The lab keeps the pain visible.

**Visual:** short bullet list; link on backup slide to recovery-gaps.md

---

### 12. How to try it / close

**On slide**

```text
pip install -r requirements.txt
python -m ui.app          # Showcase first
# tutorials: content/tutorials/
```

Repo: github.com/ryanlingo/durable-research-agent

**Say**

Start with Showcase. If the token gap is obvious without a lecture, the control plane was the product.

**Visual:** QR or URL; optional idle UI screenshot

---

## Backup slides (interview / Q&A)

| B1 | Parallel tools: gather vs concurrent Activities (post 05) |
| B2 | Evaluation in the loop (faithfulness / relevance / 0.7 gate) |
| B3 | Live mode: Crash / Resume non-Temporal; Temporal event stream |
| B4 | Crash at searching / evaluating (Showcase selector) |
| B5 | Glossary: Workflow Execution, Activity, Event History, Signal, Query |
| B6 | Recovery gap catalog (full six) |

---

## Asset checklist (copy into deck)

| Asset | Use on |
|-------|--------|
| `diagrams/02-shared-brain-two-runtimes.svg` | 5 |
| `diagrams/06-pipeline-linear.svg` | 4 |
| `diagrams/03-crash-without-temporal.svg` | 8 |
| `diagrams/04-crash-with-temporal.svg` | 9 |
| `diagrams/05-hitl-polling-vs-signal.svg` | 10 |
| `media/2026-07-31-showcase-idle.png` | 1 optional |
| `media/2026-07-31-showcase-mid-run.png` | 6 |
| `media/2026-07-31-showcase-comparison-panel.png` | 7 |
| `media/2026-07-31-temporal-web-ui.png` | 9 optional |
| `media/2026-07-31-showcase-crash-demo.mp4` | 6 if no live demo |

All paths under `content/assets/`.

---

## Open / close lines (paste into notes)

**Open:** Retries and SQLite checkpoints do not make an agent durable. They make it slightly less fragile until the process dies mid-call.

**Close:** If a crash doubles spend, the control plane is incomplete. That is a sharper signal than “we should add more logging.”

---

## Build notes

1. Keep slides B&W; match diagram STYLE (no random brand colors).  
2. Prefer SVG in Keynote/PowerPoint when possible; PNG exports exist for every diagram.  
3. Do not read the recovery-gap list in the short talk; one example (mid-write) is enough.  
4. If the room has no network, Showcase needs none. Live mode and Temporal Web UI need local services.  
5. After export, drop `YYYY-MM-DD-durable-agents-crash-lab.pptx` (or `.key`/PDF) next to this outline and add a row to `content/assets/media/LINKS.md` if hosted.

## Related

- Tutorials: [`../tutorials/`](../tutorials/)  
- Loom script: [`../assets/loom-crash-demo.md`](../assets/loom-crash-demo.md)  
- Series: [`../series/durable-agents.md`](../series/durable-agents.md)  
- Launch social: [`../social/launch-thread.md`](../social/launch-thread.md)  
