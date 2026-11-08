"""Run the official authoring preflight for legacy single-pair splits.

Some canonical records encode ``test`` as one pair object rather than a list.
The shared authoring checker currently iterates the object as though it were a
list.  This task-local shim normalizes that read-only view, then delegates all
source binding, protected-Racket execution, and receipt writing to the official
``arcpuzzles.review_base_preflight`` implementation.  It never edits canonical
records or the shared runtime.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable


def normalize_record_splits(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return shallow record copies whose train/test splits are always lists."""
    normalized: list[dict[str, Any]] = []
    for record in records:
        if type(record) is not dict:
            raise ValueError("canonical records must be objects")
        copied = dict(record)
        for split in ("train", "test"):
            value = copied.get(split, [])
            if type(value) is dict:
                copied[split] = [value]
            elif type(value) is list:
                copied[split] = list(value)
            else:
                raise ValueError(f"canonical {split} split must be a pair or list")
        normalized.append(copied)
    return normalized


def preflight(root: Path, task_id: str, out: Path, demos: int | None = None) -> dict[str, Any]:
    """Delegate to the official preflight with a scoped legacy-shape adapter."""
    from arcpuzzles import review_base_preflight as official

    original_base_checks = official._base_checks
    original_records = official._records

    def compatible_base_checks(catalog: Any, selected: str) -> dict[str, Any]:
        def normalized_records(inner_catalog: Any, inner_selected: str) -> list[dict[str, Any]]:
            return normalize_record_splits(original_records(inner_catalog, inner_selected))

        official._records = normalized_records
        try:
            report = original_base_checks(catalog, selected)
        finally:
            official._records = original_records
        # Preserve the official binding to the exact unnormalized canonical bytes.
        report["canonical_records_sha256"] = official._records_hash(catalog, selected)
        return report

    official._base_checks = compatible_base_checks
    try:
        return official.preflight(root, task_id, out, demos=demos)
    finally:
        official._base_checks = original_base_checks
        official._records = original_records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    report = preflight(args.root, args.task_id, args.out, demos=args.demos)
    print(json.dumps({key: report[key] for key in (
        "status", "verification_status", "owner_accepted", "receipt"
    )}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
