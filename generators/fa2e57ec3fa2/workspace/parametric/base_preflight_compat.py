"""Scoped authoring-preflight bridge for a legacy single-test-pair record.

The shared preflight iterates every canonical split as a list.  This task's
immutable canonical ledger predates that convention and stores its sole test
pair directly as a mapping.  This bridge normalizes only that container shape,
then delegates to the unchanged source-binding and protected-execution path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles.catalog import Catalog
from arcpuzzles import review_base_preflight as shared

TASK_ID = "fa2e57ec3fa2"


def normalized_split(record, split):
    value = record.get(split, [])
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"canonical {split} must be a pair object or list of pairs")


def fixed_base_checks(catalog, tid):
    """Shared `_base_checks`, with only legacy split-container normalization."""
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

    row = catalog.describe(tid)
    records = shared._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")
    pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(normalized_split(record, split)):
                        if "output" not in pair:
                            continue
                        grid = lambda value: (
                            _grid([[int(cell) for cell in line] for line in value])
                            if value and isinstance(value[0], str)
                            else _grid(value)
                        )
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
        "canonical_records_sha256": shared._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "compatibility": {
            "schema": "fa2e-single-test-pair-normalization-v1",
            "scope": "container shape only; canonical pair bytes and labels unchanged",
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    if args.task_id != TASK_ID:
        raise ValueError(f"compatibility bridge is scoped to {TASK_ID}")
    original = shared._base_checks
    shared._base_checks = fixed_base_checks
    try:
        report = shared.preflight(args.root, args.task_id, args.out, demos=args.demos)
    finally:
        shared._base_checks = original
    print(json.dumps({key: report[key] for key in (
        "status", "verification_status", "owner_accepted", "receipt"
    )}))


if __name__ == "__main__":
    main()
