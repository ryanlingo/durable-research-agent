#!/usr/bin/env python3
"""Approve or reject a pending non-Temporal research run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from without_temporal.state import set_approval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("status", choices=["approved", "rejected"])
    args = parser.parse_args()
    set_approval(args.run_id, args.status)
    print(f"Set {args.run_id} → {args.status}")


if __name__ == "__main__":
    main()
