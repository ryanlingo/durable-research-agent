#!/usr/bin/env python3
"""Temporal worker for the durable research agent."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from temporalio.client import Client
from temporalio.worker import Worker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from with_temporal.activities import (
    clarify_activity,
    evaluate_activity,
    plan_activity,
    retrieve_activity,
    search_activity,
    write_activity,
)
from with_temporal.workflows import ResearchWorkflow

TASK_QUEUE = "research-agent-task-queue"


async def main() -> None:
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ResearchWorkflow],
        activities=[
            clarify_activity,
            plan_activity,
            retrieve_activity,
            search_activity,
            write_activity,
            evaluate_activity,
        ],
    )
    print(f"Worker started on task queue '{TASK_QUEUE}'")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
