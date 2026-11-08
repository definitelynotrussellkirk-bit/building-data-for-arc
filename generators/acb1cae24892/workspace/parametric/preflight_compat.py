"""Run the official base preflight with one legacy pair-shape normalization.

The selected canonical stores its single ``test`` pair as an object while the
packet's shared base-check loop assumes every split is a list.  This wrapper
changes only that iteration boundary: one pair object becomes a one-element
list.  It delegates source binding, canonical hashing, ordinary generation,
protected Racket execution, parametric checks, receipt construction, and all
source-change guards to the official preflight.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles import review_base_preflight as official


def pair_list(value):
    """Return a split as a list without changing any pair/program bytes."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError("canonical train/test pairs must be a list or one pair object")


def _base_checks_compat(catalog, tid):
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    row = catalog.describe(tid)
    records = official._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")

    pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(pair_list(record.get(split, []))):
                        if "output" not in pair:
                            continue

                        def grid(value):
                            if value and isinstance(value[0], str):
                                value = [[int(cell) for cell in line] for line in value]
                            return _grid(value)

                        actual = _grid(apply(record["program_solution"], grid(pair["input"])))
                        if actual != grid(pair["output"]):
                            raise ValueError(
                                f"Original label mismatch: variant {variant} {split}[{index}]"
                            )
                        pairs.append(
                            {
                                "variant": variant,
                                "split": split,
                                "index": index,
                                "input": grid(pair["input"]),
                                "output": actual,
                            }
                        )
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
        "canonical_records_sha256": official._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "compatibility": {
            "schema": "arcpuzzles-single-pair-object-normalization-v1",
            "scope": "iteration shape only; labels and programs unchanged",
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)

    original = official._base_checks
    try:
        official._base_checks = _base_checks_compat
        report = official.preflight(args.root, args.task_id, args.out, demos=args.demos)
    finally:
        official._base_checks = original

    print(
        json.dumps(
            {
                key: report[key]
                for key in ("status", "verification_status", "owner_accepted", "receipt")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
