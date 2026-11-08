"""Task-local authoring-preflight compatibility for a legacy singleton test pair.

The canonical 6d095613d305 ledger stores ``test`` as one pair mapping rather
than a list.  The packet's generic authoring preflight iterates split values
as lists, so this wrapper changes only the base-label inspection for this task.
It preserves the original record hash and delegates all source binding,
parametric execution, and receipt construction to the packet implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from arcpuzzles import review_base_preflight as author

TASK_ID = "6d095613d305"


def split_pairs(record: dict, split: str) -> list[dict]:
    """Normalize the task's legacy single-pair mapping without mutating it."""
    pairs = record.get(split, [])
    if pairs is None:
        return []
    if isinstance(pairs, dict):
        return [pairs]
    if isinstance(pairs, list):
        return pairs
    raise ValueError(f"{split} must be a pair mapping or list of pair mappings")


def base_checks(catalog, tid: str) -> dict:
    """Run the stock base checks with singleton split normalization only."""
    if tid != TASK_ID:
        raise ValueError(f"compatibility wrapper is scoped to {TASK_ID}")
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    row = catalog.describe(tid)
    records = author._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")

    checked_pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(split_pairs(record, split)):
                        if "output" not in pair:
                            continue

                        def grid(value):
                            if value and isinstance(value[0], str):
                                return _grid([[int(cell) for cell in line] for line in value])
                            return _grid(value)

                        actual = _grid(apply(record["program_solution"], grid(pair["input"])))
                        if actual != grid(pair["output"]):
                            raise ValueError(
                                f"Original label mismatch: variant {variant} {split}[{index}]"
                            )
                        checked_pairs.append(
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

    if not checked_pairs:
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
        "pairs": checked_pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "compatibility": "normalized legacy singleton test mapping",
    }


def preflight(root: Path, tid: str, out: Path, *, demos: int | None = None) -> dict:
    """Delegate to the stock preflight while replacing one scoped check."""
    if tid != TASK_ID:
        raise ValueError(f"compatibility wrapper is scoped to {TASK_ID}")
    original = author._base_checks
    author._base_checks = base_checks
    try:
        return author.preflight(root, tid, out, demos=demos)
    finally:
        author._base_checks = original


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    report = preflight(args.root, args.task_id, args.out, demos=args.demos)
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
