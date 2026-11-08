"""Task-local launcher for singleton-query canonical records.

The packet's shared ``review_base_preflight`` currently assumes every canonical
``train``/``test`` field is a list.  This task uses the also-supported ARC form
where a single test pair is stored directly as a mapping.  The launcher keeps
all shared preflight checks and evidence schemas unchanged, normalizing only
that in-memory container shape while preserving the raw canonical-record hash
used by the preflight's source-change guard.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from arcpuzzles import review_base_preflight as shared

_ORIGINAL_BASE_CHECKS = shared._base_checks
_ORIGINAL_RECORDS = shared._records
_ORIGINAL_RECORDS_HASH = shared._records_hash


def normalized_pairs(record: dict[str, Any], split: str) -> list[dict[str, Any]]:
    """Return a list for either canonical list or singleton-mapping storage."""
    value = record.get(split, [])
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or not all(isinstance(pair, dict) for pair in value):
        raise TypeError(f"canonical {split} must be a pair mapping or list of pair mappings")
    return value


def _normalized_records(catalog, task_id: str) -> list[dict[str, Any]]:
    records = _ORIGINAL_RECORDS(catalog, task_id)
    return [
        {
            **record,
            "train": normalized_pairs(record, "train"),
            "test": normalized_pairs(record, "test"),
        }
        for record in records
    ]


def _compatible_base_checks(catalog, task_id: str) -> dict[str, Any]:
    # The shared implementation calls its module-level _records helper. Swap in
    # the shape-normalizing projection only for that call, then restore it.
    shared._records = _normalized_records
    try:
        result = _ORIGINAL_BASE_CHECKS(catalog, task_id)
    finally:
        shared._records = _ORIGINAL_RECORDS
    # Keep the preflight's later source-change comparison bound to the exact raw
    # canonical record rather than the normalized in-memory projection.
    result["canonical_records_sha256"] = _ORIGINAL_RECORDS_HASH(catalog, task_id)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args()

    shared._base_checks = _compatible_base_checks
    try:
        report = shared.preflight(
            args.root,
            args.task_id,
            args.out,
            demos=args.demos,
        )
    finally:
        shared._base_checks = _ORIGINAL_BASE_CHECKS
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "verification_status",
                    "owner_accepted",
                    "receipt",
                )
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
