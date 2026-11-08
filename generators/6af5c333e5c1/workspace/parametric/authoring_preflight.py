#!/usr/bin/env python3
"""Compatibility authoring preflight for canonical records with a mapping-valued test.

The shared preflight currently assumes every ``test`` member is a list. Some
bank records store one labelled test pair directly as a mapping. This wrapper
runs the same source binding, original-label replay, ordinary generation and
protected parametric execution while normalizing only that container shape.
It writes the standard authoring-preflight receipt consumed by native witness
and public-preview helpers; it grants no approval or acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

from arcpuzzles.catalog import Catalog
from arcpuzzles import parametric_promotion as native
from arcpuzzles.parametric_worker import _grid, _local_imports, _real_evaluator
from arcpuzzles.review_base_preflight import (
    POLICY,
    SCHEMA,
    _records,
    _records_hash,
    source_ready,
)
from arcpuzzles.review_parametric_admission import qualification_demo_count


def _pairs(record: dict[str, Any], split: str) -> Iterator[dict[str, Any]]:
    """Yield labelled pairs from either the normal list or legacy single mapping."""
    value = record.get(split, [])
    if isinstance(value, dict):
        yield value
        return
    if isinstance(value, list):
        yield from value
        return
    raise ValueError(f"{split} must be a pair mapping or list of pair mappings")


def _base_checks(catalog: Catalog, task_id: str) -> dict[str, Any]:
    row = catalog.describe(task_id)
    records = _records(catalog, task_id)
    programs = {record["program_solution"] for record in records}
    if len(programs) != 1:
        raise ValueError("Base review needs one exact canonical program")
    retained: list[dict[str, Any]] = []
    with _local_imports(catalog.root / "shared/runtime", catalog.root / "generators" / task_id):
        apply, identity, bridge = _real_evaluator(catalog.root / "shared/runtime")
        try:
            for variant, record in enumerate(records):
                for split in ("train", "test"):
                    for index, pair in enumerate(_pairs(record, split)):
                        if not isinstance(pair, dict) or "output" not in pair:
                            continue
                        normalize = lambda value: _grid(
                            [[int(char) for char in line] for line in value]
                        ) if value and isinstance(value[0], str) else _grid(value)
                        source = normalize(pair["input"])
                        actual = _grid(apply(record["program_solution"], source))
                        if actual != normalize(pair["output"]):
                            raise ValueError(
                                f"Original label mismatch: variant {variant} {split}[{index}]"
                            )
                        retained.append({
                            "variant": variant,
                            "split": split,
                            "index": index,
                            "input": source,
                            "output": actual,
                        })
        finally:
            bridge.close()
    if not retained:
        raise ValueError("Base review needs labelled original pairs")
    draws = [
        catalog.generate(
            task_id,
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
        "canonical_records_sha256": _records_hash(catalog, task_id),
        "pairs": retained,
        "generation": draws,
        "racket": identity,
        "base_approved_before": row["approved"],
        "container_compatibility": "mapping-valued test normalized to one pair",
    }


def preflight(root: Path, task_id: str, out: Path, *, demos: int | None = None, timeout: int = 180) -> dict[str, Any]:
    root = Path(root).resolve()
    out = Path(out)
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    catalog = Catalog(root)
    contract, binding = source_ready(root, task_id)
    demos = qualification_demo_count(contract, demos)
    if not 2 <= demos <= 6:
        raise ValueError("Declare a teachable count within 2..6 demonstrations")
    jobs = [
        job
        for setting in native.settings_space(contract)
        for seed in (0, 17)
        for job in native._jobs(
            contract,
            seed=seed,
            count=1,
            demos=demos,
            queries=4,
            settings=setting,
        )
    ]
    base = _base_checks(catalog, task_id)
    execution = native._execute(catalog, task_id, contract, jobs, timeout)
    programs = native._check_execution(execution, jobs, binding, contract)
    execution["base_review"] = base
    for episode in execution["episodes"]:
        episode["reference"] = "unapproved_authoring_preflight"
    if source_ready(root, task_id) != (contract, binding):
        raise ValueError("Source changed during authoring preflight")
    if _records_hash(Catalog(root), task_id) != base["canonical_records_sha256"]:
        raise ValueError("Canonical records changed during authoring preflight")
    out.mkdir(parents=True, exist_ok=False)
    native._write(out / "execution.json", execution)
    report = {
        "schema": SCHEMA,
        "status": "passed",
        "task_id": task_id,
        "verification_status": "authoring_preflight_not_owner_qualification",
        "owner_accepted": False,
        "training_admitted": False,
        "source_binding": binding,
        "contract": contract,
        "jobs": jobs,
        "programs": programs,
        "execution": {
            "path": "execution.json",
            "sha256": hashlib.sha256((out / "execution.json").read_bytes()).hexdigest(),
        },
        "limits": (
            "Finite base/reference and parametric checks. Adversarial self-review still "
            "required; owner source review and native admission remain separate."
        ),
        "compatibility_note": (
            "Used the standard protected authoring pipeline with one legacy mapping-valued "
            "test pair normalized to a singleton sequence."
        ),
        "base_review_policy": POLICY,
    }
    native._write(out / "qualification.json", report)
    return {**report, "receipt": str((out / "qualification.json").resolve())}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demos", type=int)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    report = preflight(args.root, args.task_id, args.out, demos=args.demos, timeout=args.timeout)
    print(json.dumps({
        key: report[key]
        for key in ("status", "verification_status", "owner_accepted", "receipt")
    }))


if __name__ == "__main__":
    main()
