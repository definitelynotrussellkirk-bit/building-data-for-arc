#!/usr/bin/env python3
"""Source-bound evidence for canonical-fitting shortcut rules.

The probe deliberately reads the generator's actual ``CANONICAL_SHORTCUTS``,
``SEMANTIC_WITNESSES`` and authoritative mirror instead of duplicating a rival
name list.  With ``--racket`` it also executes the selected canonical Racket
program on the retained exact counterexample.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any

from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
)

TASK_ID = "5419b6df2873"
BANDS = ("easy", "medium", "hard")


def _grid_hash(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def _canonical_program(root: Path) -> str:
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise RuntimeError(f"canonical program missing for {TASK_ID}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def _racket_callable(source: str) -> str:
    stripped = source.strip()
    if not stripped.startswith("(rule!") or not stripped.endswith(")"):
        raise ValueError("this task probe expects a single `(rule! BODY)` program")
    body = stripped[len("(rule!") : -1].strip()
    return f"(lambda (g) {body})"


def _racket_application(source: str, grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(str(value) for value in row) + ")" for row in grid)
    return f"({_racket_callable(source)} '({rows}))"


def _differences(left: list[list[int]], right: list[list[int]]) -> list[dict[str, int]]:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("comparison outputs must have identical shapes")
    return [
        {"row": row, "column": column, "intended": left[row][column], "rival": right[row][column]}
        for row in range(len(left))
        for column in range(len(left[0]))
        if left[row][column] != right[row][column]
    ]


def build_report(
    *,
    seed: int,
    sample_index: int,
    difficulty: str,
    per_band: int,
    run_racket: bool,
) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in BANDS:
        raise ValueError(f"difficulty must be one of {BANDS}")
    if type(per_band) is not int or per_band < 1:
        raise ValueError("per_band must be a positive integer")

    root = find_root(__file__)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    canonical = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    shortcuts = dict(getattr(generator, "CANONICAL_SHORTCUTS", {}))
    witnesses = dict(getattr(generator, "SEMANTIC_WITNESSES", {}))
    if not shortcuts:
        raise RuntimeError("generator declares no CANONICAL_SHORTCUTS")
    if not witnesses:
        raise RuntimeError("generator declares no SEMANTIC_WITNESSES")

    canonical_fit: dict[str, Any] = {}
    for name, rival in shortcuts.items():
        checks = [rival(pair["input"]) == pair["output"] for pair in canonical]
        canonical_fit[name] = {
            "fits_all": all(checks),
            "pairs_fit": sum(checks),
            "pairs_total": len(checks),
        }

    grid = generator.generate(seed, sample_index, difficulty=difficulty)
    grammar_errors = generator.self_check(grid)
    if grammar_errors:
        raise RuntimeError(f"generated exact counterexample failed self_check: {grammar_errors}")
    intended = generator.authoritative_output(grid)
    firing_witnesses = sorted(name for name, predicate in witnesses.items() if predicate(grid))
    rival_outputs = {name: rival(grid) for name, rival in shortcuts.items()}
    all_differences = {
        name: _differences(intended, output) for name, output in rival_outputs.items()
    }

    canonical_program = _canonical_program(root)
    racket_output = None
    racket_runtime = None
    if run_racket:
        from arc_repl.racket_bridge import RacketBridge

        bridge = RacketBridge(timeout=30, max_calls_before_restart=32)
        try:
            racket_runtime = bridge.runtime_identity
            racket_output = bridge.eval_text(_racket_application(canonical_program, grid))
        finally:
            bridge.shutdown()
        if racket_output != intended:
            raise RuntimeError("canonical Racket output disagrees with authoritative_output")

    rival_disagreements = {name: 0 for name in shortcuts}
    witness_hits = 0
    unique_inputs: set[str] = set()
    per_band_rows: dict[str, Any] = {}
    for band in BANDS:
        band_witnesses = 0
        band_disagreements = {name: 0 for name in shortcuts}
        for offset in range(per_band):
            candidate = generator.generate(seed + 1000 + offset, offset, difficulty=band)
            unique_inputs.add(_grid_hash(candidate))
            official = generator.authoritative_output(candidate)
            fires = any(predicate(candidate) for predicate in witnesses.values())
            witness_hits += int(fires)
            band_witnesses += int(fires)
            for name, rival in shortcuts.items():
                disagrees = rival(candidate) != official
                rival_disagreements[name] += int(disagrees)
                band_disagreements[name] += int(disagrees)
        per_band_rows[band] = {
            "samples": per_band,
            "witness_hits": band_witnesses,
            "rival_disagreements": band_disagreements,
        }

    total = per_band * len(BANDS)
    exact = {
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": difficulty,
        "input": grid,
        "input_sha256": _grid_hash(grid),
        "self_check_errors": grammar_errors,
        "witnesses": firing_witnesses,
        "intended_output": intended,
        "racket_output": racket_output,
        "rivals": rival_outputs,
        "difference_cells_by_rival": all_differences,
        "difference_cells": sorted(
            {
                (row["row"], row["column"], row["intended"], row["rival"])
                for rows in all_differences.values()
                for row in rows
            }
        ),
    }

    failures = []
    for name, row in canonical_fit.items():
        if not row["fits_all"]:
            failures.append(f"declared canonical shortcut {name!r} does not fit every canonical pair")
        if not all_differences[name]:
            failures.append(f"exact generated input does not refute {name!r}")
    if not firing_witnesses:
        failures.append("exact generated input fires no declared semantic witness")
    if witness_hits != total:
        failures.append(f"only {witness_hits}/{total} sampled inputs fired a witness")

    return {
        "schema": "5419b6df2873-shortcut-probe-v1",
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "task_id": TASK_ID,
        "generator_source": str(source_path.relative_to(root)),
        "generator_sha256": source_sha256,
        "rule_hash_declared": getattr(generator, "RULE_HASH", None),
        "canonical_program_normalized_sha256": _normalized_hash(canonical_program),
        "canonical_fit": canonical_fit,
        "exact_counterexample": exact,
        "racket_checked": run_racket,
        "racket_runtime": racket_runtime,
        "emission_probe": {
            "seed_formula": "seed + 1000 + offset; sample_index = offset",
            "per_band": per_band_rows,
            "total": total,
            "unique_inputs": len(unique_inputs),
            "witness_hits": witness_hits,
            "rival_disagreements": rival_disagreements,
        },
        "limits": [
            "The emission probe is finite and covers only the declared rivals.",
            "Canonical fit uses all currently labeled canonical train/test pairs.",
            "Racket execution is performed only for the retained exact counterexample.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--difficulty", choices=BANDS, default="medium")
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    report = build_report(
        seed=args.seed,
        sample_index=args.sample_index,
        difficulty=args.difficulty,
        per_band=args.per_band,
        run_racket=args.racket,
    )
    report["cwd"] = os.getcwd()
    report["argv"] = sys.argv
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "out": str(out),
        "generator_sha256": report["generator_sha256"],
        "emission_probe": report["emission_probe"],
    }))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
