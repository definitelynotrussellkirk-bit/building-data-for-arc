"""Run authoring preflight while normalizing legacy singleton split records.

Some legacy canonical records store a single ``test`` pair as a dictionary while
``review_base_preflight`` iterates both splits as lists.  This launcher changes
only the in-memory view used by that process; it never rewrites catalog data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def normalize_records(records):
    """Return shallow record copies with train/test represented as pair lists."""
    normalized = []
    for record in records:
        copy = dict(record)
        for split in ("train", "test"):
            value = copy.get(split, [])
            if isinstance(value, dict):
                if "input" not in value:
                    raise TypeError(f"{split} singleton must be an input/output pair")
                value = [value]
            elif not isinstance(value, list):
                raise TypeError(f"{split} must be a pair list or singleton pair")
            copy[split] = value
        normalized.append(copy)
    return normalized


def main() -> int:
    from arcpuzzles import review_base_preflight as preflight

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args()

    original_records = preflight._records
    original_base_checks = preflight._base_checks

    def compatible_base_checks(catalog, task_id):
        def compatible_records(inner_catalog, inner_task_id):
            return normalize_records(original_records(inner_catalog, inner_task_id))

        preflight._records = compatible_records
        try:
            result = original_base_checks(catalog, task_id)
        finally:
            preflight._records = original_records
        # Keep the public receipt bound to the unchanged raw catalog bytes so
        # downstream witness/preview helpers can perform their normal drift check.
        result["canonical_records_sha256"] = preflight._records_hash(catalog, task_id)
        return result

    preflight._base_checks = compatible_base_checks
    report = preflight.preflight(args.root, args.task_id, args.out, demos=args.demos)
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
