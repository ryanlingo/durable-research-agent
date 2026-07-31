# Diagrams

Minimal architecture diagrams in the style of the project reference (white canvas, thin black strokes, rounded nodes, stacked diamonds with progressive dotted borders).

| File | Use |
|------|-----|
| `01-research-agent-stack.svg` | Query → agent → report with plan / tools / evaluate / approval |
| `02-shared-brain-two-runtimes.svg` | Shared logic split into without / with Temporal |
| `03-crash-without-temporal.svg` | Crash mid-write and costly recovery |
| `04-crash-with-temporal.svg` | Worker crash and resume from history |
| `05-hitl-polling-vs-signal.svg` | Polling process vs Signal wait |
| `06-pipeline-linear.svg` | Flat pipeline strip for slides |

Source of truth: SVG. PNG exports sit beside them for embeds that need raster.

Style rules: `STYLE.md` (same visual language as the reference screenshot).

Regenerate PNGs:

```bash
source .venv/bin/activate
pip install cairosvg
python content/assets/diagrams/render_png.py
```
