# Content studio

Writing and teaching assets derived from this repo.

- Voice: local `context/STYLE.md`
- Temporal terms: [`concepts/temporal-concepts.md`](concepts/temporal-concepts.md)
- Labels on diagrams and in copy: [`assets/diagrams/STYLE.md`](assets/diagrams/STYLE.md) (canonical Temporal terms first; reuse plain language after)
- Messaging: [`concepts/feature-benefit-outcome.md`](concepts/feature-benefit-outcome.md) (Feature → Benefit → Outcome)

## Layout

| Path | Role |
|------|------|
| `concepts/` | Temporal vocabulary, FBO messaging, recovery-gap catalog |
| `drafts/` | Long-form blog posts (01–05 ready) |
| `tutorials/` | Step-by-step how-tos (01 Showcase, 02 non-Temporal crash, 03 Temporal Worker) |
| `decks/` | Slide decks and outlines (crash-lab outline ready) |
| `social/` | LinkedIn / X cuts |
| `series/` | Multi-post arcs and calendar |
| `notes/` | Day-of observations from demos |
| `assets/diagrams/` | Infographics (SVG + PNG) |
| `assets/media/` | Screenshots, recordings, GIFs |
| `assets/loom-crash-demo.md` | Recording shot list |

## Working rule

When a behavior becomes visible (crash, token gap, Signal wait, Event History):

1. Short note in `notes/`
2. Promote into a draft, tutorial, or deck outline
3. Reuse diagrams from `assets/diagrams/`; drop captures into `assets/media/`
4. Refresh social only if the hook changed

Before commit, run the final edit checklist in `context/STYLE.md` and the FBO checklist in `concepts/feature-benefit-outcome.md`.
