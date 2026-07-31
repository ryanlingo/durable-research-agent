#!/usr/bin/env python3
"""Start a Temporal research workflow and optionally wait for the result."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from temporalio.client import Client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from with_temporal.worker import TASK_QUEUE
from with_temporal.workflows import ResearchWorkflow


async def main() -> None:
    parser = argparse.ArgumentParser(description="Temporal research agent client")
    parser.add_argument(
        "query",
        nargs="?",
        default="How does durable execution help AI agents?",
    )
    parser.add_argument("--workflow-id", default=None)
    parser.add_argument("--auto-approve", action="store_true")
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Block until the workflow completes (only useful with --auto-approve)",
    )
    args = parser.parse_args()

    client = await Client.connect("localhost:7233")
    workflow_id = args.workflow_id or f"research-{uuid.uuid4().hex[:8]}"

    handle = await client.start_workflow(
        ResearchWorkflow.run,
        args=[args.query, args.auto_approve],
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    print(f"Started workflow: {workflow_id}")
    print(f"Query status : temporal workflow query --workflow-id {workflow_id} status")
    print(f"Approve      : python -m with_temporal.signal_approval {workflow_id} approved")
    print(f"Clarify      : python -m with_temporal.signal_clarify {workflow_id} \"your answers\"")

    if args.wait:
        result = await handle.result()
        print("\n===== RESULT =====")
        print(result.get("markdown_report", result))
        print("\n===== META =====")
        print(f"Tokens: {result.get('total_tokens')}")
        print(f"Eval: {result.get('evaluation')}")


if __name__ == "__main__":
    asyncio.run(main())
