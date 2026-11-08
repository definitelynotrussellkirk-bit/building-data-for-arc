"""Compatibility launcher for packet authoring preflight singleton test splits.

The packet's canonical JSON represents one-query ``test`` splits as a single
pair object, while the bundled ``review_base_preflight._base_checks`` assumes a
list and iterates the keys ``input`` and ``output``.  This launcher changes only
that iteration boundary: singleton pair objects become one-element lists.  All
source binding, canonical-record hashing, protected-Racket execution, parametric
worker checks, and receipt writing remain the bundled implementation.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from arcpuzzles import review_base_preflight as upstream


def _split_pairs(record, split):
    value = record.get(split, [])
    if isinstance(value, dict):
        if set(value) < {"input", "output"}:
            raise ValueError(f"singleton {split} pair is missing input/output")
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"{split} split must be a pair object or list of pairs")


def _base_checks(catalog, tid):
    """Upstream base checks with only singleton/list split normalization."""
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

    row = catalog.describe(tid)
    records = upstream._records(catalog, tid)
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
                        if "output" not in pair:
                            continue
                        grid = (
                            lambda value: _grid([[int(cell) for cell in line] for line in value])
                            if value and isinstance(value[0], str)
                            else _grid(value)
                        )
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
        "canonical_records_sha256": upstream._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "compatibility": {
            "scope": "normalize singleton canonical split objects to one-element lists",
            "upstream_behavior_otherwise_unchanged": True,
        },
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    args = parser.parse_args(argv)
    upstream._base_checks = _base_checks
    report = upstream.preflight(
        args.root,
        args.task_id,
        args.out,
        demos=args.demos,
    )
    import json

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
