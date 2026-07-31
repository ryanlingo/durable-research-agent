# Contributing

Thanks for interest in improving this lab. The goal is a fair, reproducible comparison between a typical agent stack and Temporal Durable Execution—not a feature race.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
cp .env.example .env
```

## Checks before you open a PR

1. **Fairness** - if you change one implementation’s behavior, consider the other. Shared logic belongs in `shared/`.
2. **Vocabulary** - Temporal terms must match [`content/concepts/temporal-concepts.md`](content/concepts/temporal-concepts.md) and the [Temporal glossary](https://docs.temporal.io/glossary). Prefer/avoid labels: [`content/assets/diagrams/STYLE.md`](content/assets/diagrams/STYLE.md).
3. **Messaging** - audience-facing copy should support Feature → Benefit → Outcome ([`content/concepts/feature-benefit-outcome.md`](content/concepts/feature-benefit-outcome.md)).
4. **Style** - prose is direct and specific; avoid marketer filler.
5. **Secrets** - never commit `.env` or API keys.

```bash
# when tests are present
pytest
ruff check .
```

## Layout

| Area | Own it if you change… |
|------|------------------------|
| `shared/` | tools, RAG, eval, types, config |
| `without_temporal/` | checkpoint / polling path |
| `with_temporal/` | Workflow, Activities, Worker, Signals |
| `ui/` | experiment dashboard |
| `content/` | teaching assets |
| `demos/` | crash procedures |

## Design constraints

- Non-Temporal path keeps realistic retries and checkpoints (not a strawman).
- RAG stays on the fixed local corpus unless you document a demo-stable alternative.
- Prefer small, reviewable PRs that each prove one behavior.

## License

By contributing, you agree your contributions are licensed under the MIT License.
