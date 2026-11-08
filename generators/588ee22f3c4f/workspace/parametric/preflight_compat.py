"""Narrow compatibility launcher for the packet's authoring preflight.

The packet helper assumes every canonical train/test split is a list.
This task's immutable canonical record uses the common ARC shape where test
is one pair object.  The launcher patches only the in-memory base-label loop to
view that singleton as a one-item sequence, then delegates source binding,
parametric jobs, protected Racket execution, report writing, and drift checks to
arcpuzzles.review_base_preflight unchanged.  It never rewrites the catalog.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

HOME = Path(__file__).resolve().parent
ROOT = HOME.parents[3]
TASK_ID = "588ee22f3c4f"

for candidate in (ROOT / "src", ROOT / "shared" / "runtime"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from arcpuzzles import review_base_preflight as official


def _split_pairs(record: dict[str, Any], split: str) -> list[dict[str, Any]]:
    """Return one canonical split without changing the immutable record."""
    value = record.get(split, [])
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(pair, dict) for pair in value):
        return value
    raise TypeError(f"canonical {split} must be a pair object or list of pair objects")


def _base_checks_compat(catalog, tid: str) -> dict[str, Any]:
    """Official base checks with singleton split normalization only."""
    from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator

    row = catalog.describe(tid)
    records = official._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")

    def normalized_grid(value):
        if value and isinstance(value[0], str):
            value = [[int(cell) for cell in line] for line in value]
        return _grid(value)

    pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(_split_pairs(record, split)):
                        if "output" not in pair:
                            continue
                        actual = _grid(
                            apply(record["program_solution"], normalized_grid(pair["input"]))
                        )
                        if actual != normalized_grid(pair["output"]):
                            raise ValueError(
                                f"Original label mismatch: variant {variant} {split}[{index}]"
                            )
                        pairs.append(
                            {
                                "variant": variant,
                                "split": split,
                                "index": index,
                                "input": normalized_grid(pair["input"]),
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
            "schema": "arcpuzzles-singleton-test-split-compat-v1",
            "catalog_rewritten": False,
            "change": "treat a singleton test pair object as a one-item sequence",
        },
    }


def run(root: Path, out: Path, *, demos: int | None = None) -> dict[str, Any]:
    prior = official._base_checks
    official._base_checks = _base_checks_compat
    try:
        return official.preflight(root, TASK_ID, out, demos=demos)
    finally:
        official._base_checks = prior


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    report = run(args.root, args.out, demos=args.demos)
    print(
        json.dumps(
            {key: report[key] for key in ("status", "verification_status", "owner_accepted", "receipt")}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
