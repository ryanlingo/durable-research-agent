# Diagram style (match reference screenshot)

Visual system for all architecture / sequence diagrams in this project.

## Look

- White or near-white canvas (`#FFFFFF` / `#FAFAFA`)
- Thin dark strokes (`#1A1A1A`, ~1.5–2px)
- Primary filled node: light gray fill (`#E8E8E8` or `#F0F0F0`)
- Secondary nodes: white fill, solid stroke
- Optional / weaker layers: white fill, **dotted** stroke (increasing dash gap as importance drops)
- Rounded rectangles for process nodes (`rx` ≈ 12–16)
- Diamonds for stacked capabilities or decision-adjacent layers
- Arrowheads small, open or filled triangle, same stroke color
- Typography: clean sans (Inter, Helvetica, system-ui), regular weight, dark gray/black
- No gradients, no drop shadows, no colored accents unless a diagram needs a single contrast pair
- Generous whitespace; no decorative icons

## Structure patterns

1. **Horizontal flow**: Input → Core → Output (core may be filled)
2. **Vertical stack under core**: solid diamonds first, then dotted for secondary layers
3. **Side-by-side comparison**: two columns, identical visual language, only labels/content change

## Source of truth

Edit the `.svg` files in this folder. Prefer SVG over raster so text stays sharp in blogs and slides. Export PNG only when a platform requires it.

## Labels and copy (all writing that names Temporal)

Diagram text **and** captions, drafts, tutorials, decks, social, demos, and UI strings that describe Temporal should match [`content/concepts/temporal-concepts.md`](../../concepts/temporal-concepts.md) and the [Temporal glossary](https://docs.temporal.io/glossary).

**Introduce the canonical term, then reuse plain language.** After you have named Activity, Event History, Worker Process, Signal, or Query, it is fine to say step, history, worker, message, or status when the referent is already clear. Reuse key terms freely. Do not invent a second product vocabulary.

| Canonical (first mention / diagram labels) | Reuse freely once clear |
|--------------------------------------------|-------------------------|
| Workflow Execution | the execution, this run, the workflow |
| Workflow Definition / Type | the workflow code, ResearchWorkflow |
| Activity | that work, that call, the step (when it is an Activity) |
| Event History | the history, what already happened |
| Worker Process / Worker | the worker |
| Signal | the approval, the human reply (when it is a Signal) |
| Query | status, where the run is |
| Task Queue | the queue |
| Temporal Service | the service |
| Retry Policy | retries (when the policy is the topic) |

Still avoid:

- Calling the Worker the “Temporal process,” or saying the Workflow Execution “crashed” when only the Worker died
- Calling application logs Event History (or the reverse)
- “Cluster” for Temporal Service in new formal copy

Non-Temporal path keeps *checkpoint*, *poll*, *SQLite*. Shared words like *step* and *history* may appear on both sides; meaning comes from context.

Visual look rules above apply to diagrams only. Prose voice is `context/STYLE.md`.
