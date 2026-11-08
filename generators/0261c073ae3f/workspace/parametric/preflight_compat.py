"""Run the standard authoring preflight for canonical single-test-object records.

The packet's shared preflight iterates ``record['test']`` directly and therefore
mistakes the canonical ARC form (one test object) for an iterable of dictionary
keys.  This task-local shim changes only that split normalization.  It keeps the
original canonical-record hash, source binding, protected evaluator, receipt
schema, jobs, and output writer unchanged.
"""
from __future__ import annotations

from arcpuzzles import review_base_preflight as base


def record_pairs(record, split):
    """Return a split as a pair list without changing its stored authority."""
    value = record.get(split, [])
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return value
    raise ValueError(f"Canonical {split} split must be a list or object")


def compatible_base_checks(catalog, tid):
    """The standard base check with only dict-vs-list split normalization."""
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid

    row = catalog.describe(tid)
    records = base._records(catalog, tid)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")
    pairs = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / tid):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(record_pairs(record, split)):
                        if "output" not in pair:
                            continue
                        grid = (
                            lambda value: _grid([[int(c) for c in line] for line in value])
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
        "canonical_records_sha256": base._records_hash(catalog, tid),
        "pairs": pairs,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
    }


def install() -> None:
    base._base_checks = compatible_base_checks


def main() -> None:
    install()
    base.main()


if __name__ == "__main__":
    main()
