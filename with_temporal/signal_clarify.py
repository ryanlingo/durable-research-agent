#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from temporalio.client import Client

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from with_temporal.workflows import ResearchWorkflow


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow_id")
    parser.add_argument("answers")
    args = parser.parse_args()

    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(args.workflow_id)
    await handle.signal(ResearchWorkflow.submit_clarification, args.answers)
    print(f"Signaled clarification for {args.workflow_id}")


if __name__ == "__main__":
    asyncio.run(main())
