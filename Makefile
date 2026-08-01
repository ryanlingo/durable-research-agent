.PHONY: help install install-dev ui worker run-without run-with demo-server test lint demo check video

help:
	@echo "Targets:"
	@echo "  install       Install runtime dependencies"
	@echo "  install-dev   Install runtime + dev dependencies"
	@echo "  ui            Start experiment UI on :8765"
	@echo "  demo          Alias for ui (Showcase first look)"
	@echo "  video         Print URL for captioned demo (use with make ui)"
	@echo "  worker        Start Temporal Worker"
	@echo "  run-without   Non-Temporal auto-approve run"
	@echo "  run-with      Temporal auto-approve run (needs server + worker)"
	@echo "  demo-server   Print Temporal dev server command"
	@echo "  test          Run pytest"
	@echo "  lint          Run ruff"
	@echo "  check         lint + test (CI-local)"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -e ".[dev]"

ui:
	python -m ui.app

demo: ui

video:
	@echo ""
	@echo "  Captioned demo player (requires the UI server):"
	@echo "    1. make ui"
	@echo "    2. open http://127.0.0.1:8765/demo/watch.html"
	@echo "       (also /video or /demo)"
	@echo ""
	@echo "  Do not open watch.html via file:// or raw GitHub — the video will fail."
	@echo ""

worker:
	python -m with_temporal.worker

run-without:
	python -m without_temporal.run "How does durable execution help AI agents?" --auto-approve

run-with:
	python -m with_temporal.run "How does durable execution help AI agents?" --auto-approve --wait

demo-server:
	@echo "temporal server start-dev"

test:
	python -m pytest

lint:
	python -m ruff check shared without_temporal with_temporal ui tests

check: lint test
