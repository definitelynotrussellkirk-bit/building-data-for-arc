"""Compatibility entry point for base preflight on legacy single-test records.

Some canonical ARC rows store ``test`` as one ``{input, output}`` object rather
than a list.  The packet's shared preflight iterates that dictionary as strings.
This task-local wrapper normalizes both historical shapes, then delegates every
other source-binding and protected-Racket check to the stock preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles import review_base_preflight as author


def split_pairs(record: dict, split: str) -> list[dict]:
    value = record.get(split, [])
    if isinstance(value, dict):
        value = [value]
    if not isinstance(value, list) or any(not isinstance(pair, dict) for pair in value):
        raise ValueError(f"Invalid canonical {split} pair collection")
    return value


def base_checks(catalog: Catalog, tid: str) -> dict:
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

    row = catalog.describe(tid)
    records = author._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")
    pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(split_pairs(record, split)):
                        if "output" not in pair:
                            continue
                        grid = lambda value: _grid(
                            [[int(cell) for cell in line] for line in value]
                        ) if value and isinstance(value[0], str) else _grid(value)
                        actual = _grid(apply(record["program_solution"], grid(pair["input"])))
                        if actual != grid(pair["output"]):
                            raise ValueError(
                                f"Original label mismatch: variant {variant} {split}[{index}]"
                            )
                        pairs.append({
                            "variant": variant,
                            "split": split,
                            "index": index,
                            "input": grid(pair["input"]),
                            "output": actual,
                        })
        finally:
            bridge.close()
    if not pairs:
        raise ValueError("Base review needs labelled original pairs")
    draws = [
        catalog.generate(
            tid,
            count=1,
            seed=seed,
            difficulty=difficulty,
            n_train=2,
            n_test=1,
            allow_unapproved=True,
        )
        for seed, difficulty in ((17, None), (43, "medium"))
    ]
    return {
        "status": "passed",
        "canonical_records_sha256": author._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args()
    author._base_checks = base_checks
    report = author.preflight(args.root, args.task_id, args.out, demos=args.demos)
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
