#!/usr/bin/env python3
"""Run the official authoring preflight for a legacy singleton-test record.

The canonical JSONL format permits either a single test-pair object or a list.
Catalog.challenge already normalizes both forms, but review_base_preflight's
private _base_checks currently iterates the raw value as a list.  This task's
record uses the legacy object form.  Normalize only that in-memory record and
then invoke the unmodified official preflight/worker/source-binding pipeline.
No shared source or canonical bytes are changed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path

import arcpuzzles.review_base_preflight as official

TASK_ID = "9e2802ee78bd"
_ORIGINAL_RECORDS = official._records


def _normalized_records(catalog, tid):
    rows = deepcopy(_ORIGINAL_RECORDS(catalog, tid))
    if tid != TASK_ID:
        return rows
    for row in rows:
        tests = row.get("test")
        if isinstance(tests, dict):
            row["test"] = [tests]
        elif not isinstance(tests, list):
            raise ValueError(f"{TASK_ID}: canonical test must be an object or list")
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    official._records = _normalized_records
    report = official.preflight(
        args.root, TASK_ID, args.out, demos=args.demos
    )
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
