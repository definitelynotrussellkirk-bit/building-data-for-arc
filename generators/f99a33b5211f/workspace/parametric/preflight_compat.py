"""Run the built-base authoring preflight with legacy single-test normalization.

The packet's shared preflight assumes every canonical split is a list, while
legacy canonical records store ``test`` as one pair object.  This target-local
runner changes only that in-memory iteration shape; source binding, protected
Racket execution, hashes, schemas, and output receipts still come from the
shared preflight implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from arcpuzzles import review_base_preflight as author


def _split_pairs(record: dict[str, Any], split: str) -> list[dict[str, Any]]:
    value = record.get(split, [])
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"Canonical {split} split must be a pair object or list of pairs")


def _base_checks_compat(catalog, tid):
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
                    for index, pair in enumerate(_split_pairs(record, split)):
                        if not isinstance(pair, dict) or "output" not in pair:
                            continue
                        def grid(value):
                            if value and isinstance(value[0], str):
                                return _grid([[int(cell) for cell in line] for line in value])
                            return _grid(value)
                        actual = _grid(apply(record["program_solution"], grid(pair["input"])))
                        if actual != grid(pair["output"]):
                            raise ValueError(f"Original label mismatch: variant {variant} {split}[{index}]")
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
        "compatibility": {
            "reason": "legacy canonical test split is one pair object",
            "normalization": "dict -> one-element list for iteration only",
        },
    }


def run(root: Path, task_id: str, out: Path, demos: int | None = None, timeout: int = 180):
    original = author._base_checks
    author._base_checks = _base_checks_compat
    try:
        return author.preflight(root, task_id, out, demos=demos, timeout=timeout)
    finally:
        author._base_checks = original


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    report = run(args.root, args.task_id, args.out, demos=args.demos, timeout=args.timeout)
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
