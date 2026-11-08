#!/usr/bin/env python3
"""Run the official base preflight while accepting singleton canonical test rows.

Some older canonical records encode ``test`` as one input/output object instead
of a one-element list.  The official preflight iterates that object as strings.
This scoped runner changes only record iteration; source binding, protected
Racket execution, ordinary generation and native parametric checks remain the
official implementations.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

for _parent in Path(__file__).resolve().parents:
    if (_parent / "src/arcpuzzles").is_dir():
        sys.path.insert(0, str(_parent / "src"))
        break

from arcpuzzles import review_base_preflight as official


def split_pairs(record: dict[str, Any], split: str) -> list[dict[str, Any]]:
    value = record.get(split, [])
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"canonical {split} must be a pair object or list of pairs")


def base_checks_compat(catalog, tid):
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

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
        "canonical_records_sha256": official._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "compatibility": "singleton canonical test rows normalized to one-element lists",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args(argv)
    official._base_checks = base_checks_compat
    report = official.preflight(
        args.root,
        args.task_id,
        args.out,
        demos=args.demos,
        timeout=args.timeout,
    )
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
