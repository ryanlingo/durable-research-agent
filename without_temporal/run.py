#!/usr/bin/env python3
"""Run the non-Temporal research agent."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from without_temporal.agent import run_research


async def main() -> None:
    parser = argparse.ArgumentParser(description="Non-Temporal research agent")
    parser.add_argument("query", nargs="?", default="How does durable execution help AI agents?")
    parser.add_argument("--run-id", default=None, help="Resume an existing run_id")
    parser.add_argument("--auto-approve", action="store_true")
    args = parser.parse_args()

    report = await run_research(
        args.query,
        run_id=args.run_id,
        auto_approve=args.auto_approve,
    )
    print("\n===== REPORT =====\n")
    print(report.markdown_report)
    print("\n===== META =====")
    print(f"Tokens: {report.total_tokens.to_dict()}")
    if report.evaluation:
        print(
            f"Eval: faithfulness={report.evaluation.faithfulness:.2f} "
            f"relevance={report.evaluation.relevance:.2f} "
            f"overall={report.evaluation.overall:.2f}"
        )
        print(f"Reason: {report.evaluation.reasoning}")
    print(f"Steps: {report.steps}")


if __name__ == "__main__":
    asyncio.run(main())
