#!/usr/bin/env python3
"""Source-bound curriculum probe for ARC generator d5d9fdb01bdd.

This complements the shared semantic gate.  It checks the selected generator's
actual declarations, every three-of-four query rotation, consecutive schedule
starts, canonical-shortcut fit, exact joint boundary overrides, uniqueness, and
first concrete rival counterexamples.

Run from any directory, for example::

    python3 generators/d5d9fdb01bdd/workspace/lesson_probe.py \
        --windows-per-band 100 --out ../checks/d5d9fdb01bdd-lesson-probe.json

The probe uses ``rule_mirror`` only after the normal Racket rule-smoke stage has
established parity.  Its report hashes the exact generator bytes it imported.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "d5d9fdb01bdd"
BANDS = ("easy", "medium", "hard")
MIN_UNIQUE_FRACTION = 0.85
HERE = Path(__file__).resolve().parent
TASK_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]
GENERATOR_PATH = TASK_DIR / "generator.py"
RUNTIME = REPO_ROOT / "shared" / "runtime"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    return hashlib.sha256(
        json.dumps(grid, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(char) for char in row] for row in grid]
    return [list(row) for row in grid]


def _load_generator():
    runtime = str(RUNTIME)
    if runtime not in sys.path:
        sys.path.insert(0, runtime)
    name = f"task_probe_{TASK_ID}"
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            raw_test = row.get("test", [])
            tests = raw_test if isinstance(raw_test, list) else [raw_test]
            pairs = list(row.get("train", [])) + tests
            return [
                {
                    "input": _decode_grid(pair["input"]),
                    "output": _decode_grid(pair["output"]),
                }
                for pair in pairs
            ]
    raise RuntimeError(f"canonical task {TASK_ID} is absent")


def _pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _counterexample(gen, rival, grid) -> dict[str, Any] | None:
    intended = gen.rule_mirror(grid)
    alternate = rival(grid)
    if intended == alternate:
        return None
    return {
        "input": grid,
        "intended_output": intended,
        "rival_output": alternate,
        "input_sha256": _grid_key(grid),
    }


def _joint_override_report(gen) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    cases = 0
    for band in BANDS:
        for grid_h in (5, 11):
            for grid_w in (6, 12):
                for n_colors in (1, 3):
                    expected = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_distinct_colors": n_colors,
                    }
                    grid = gen.generate(
                        880_000 + cases,
                        cases,
                        difficulty=band,
                        **expected,
                    )
                    observed = gen.observe_overrides(grid)
                    errors = gen.self_check(grid)
                    if observed != expected or errors:
                        failures.append(
                            {
                                "band": band,
                                "expected": expected,
                                "observed": observed,
                                "self_check": errors,
                            }
                        )
                    cases += 1
    return {"cases": cases, "failures": failures}


def build_report(*, windows_per_band: int = 100, seed: int = 515_000) -> dict[str, Any]:
    if windows_per_band < 1:
        raise ValueError("windows_per_band must be positive")

    gen = _load_generator()
    canonical = _canonical_pairs()
    shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))
    witnesses = dict(getattr(gen, "SEMANTIC_WITNESSES", {}))

    canonical_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical)
        for name, rival in shortcuts.items()
    }
    counterexamples: dict[str, dict[str, Any]] = {}
    bands: dict[str, Any] = {}
    all_unique: set[str] = set()

    for band_index, band in enumerate(BANDS):
        invalid: list[dict[str, Any]] = []
        rotation_failures: list[dict[str, Any]] = []
        witness_counts = {name: 0 for name in witnesses}
        rival_refutations = {name: 0 for name in competitors}
        unique: set[str] = set()
        strict_examples = 0
        total_examples = 0

        for window in range(windows_per_band):
            lesson_seed = seed + band_index * 1_000_000 + window
            # Incrementing by one exercises every cyclic schedule start rather
            # than sampling only starts aligned to EXAMPLES_NEEDED.
            start = window
            grids = [
                gen.generate(lesson_seed, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs = [_pair(gen, grid) for grid in grids]

            for offset, grid in enumerate(grids):
                total_examples += 1
                key = _grid_key(grid)
                unique.add(key)
                all_unique.add(key)
                errors = gen.self_check(grid)
                if errors:
                    invalid.append(
                        {"window": window, "offset": offset, "errors": errors}
                    )
                strict_examples += int(not gen.strict_canonical_like(grid))
                for name, witness in witnesses.items():
                    witness_counts[name] += int(bool(witness(grid)))
                for name, rival in competitors.items():
                    candidate = _counterexample(gen, rival, grid)
                    if candidate is not None:
                        rival_refutations[name] += 1
                        counterexamples.setdefault(name, candidate)

            # Test every member as query.  This catches schedules that teach a
            # rule only because one special role is always placed in demos.
            for query_index, query in enumerate(pairs):
                demos = [
                    pair for index, pair in enumerate(pairs) if index != query_index
                ]
                surviving = gen.lesson_identifiable(demos, query)
                if surviving:
                    rotation_failures.append(
                        {
                            "window": window,
                            "start": start,
                            "query_index": query_index,
                            "surviving": surviving,
                        }
                    )

        bands[band] = {
            "windows": windows_per_band,
            "examples": total_examples,
            "unique_inputs": len(unique),
            "unique_fraction": len(unique) / total_examples,
            "strict_examples": strict_examples,
            "strict_fraction": strict_examples / total_examples,
            "witness_counts": witness_counts,
            "rival_counterexample_occurrences": rival_refutations,
            "invalid": invalid,
            "query_rotation_failures": rotation_failures,
        }

    joint_overrides = _joint_override_report(gen)
    failures: list[str] = []
    if not shortcuts:
        failures.append("no CANONICAL_SHORTCUTS declared")
    failures.extend(
        f"canonical shortcut {name!r} does not fit every canonical pair"
        for name, fits in canonical_fit.items()
        if not fits
    )
    if not competitors:
        failures.append("no LESSON_COMPETITORS declared")
    if set(counterexamples) != set(competitors):
        failures.append("at least one declared competitor has no generated counterexample")
    if joint_overrides["failures"]:
        failures.append("joint boundary overrides failed")
    for band, summary in bands.items():
        if summary["invalid"]:
            failures.append(f"{band}: invalid generated inputs")
        if summary["query_rotation_failures"]:
            failures.append(f"{band}: at least one query rotation is ambiguous")
        if summary["strict_fraction"] < gen.MIN_STRICT_FRAC:
            failures.append(f"{band}: strict canonical fraction below MIN_STRICT_FRAC")
        if summary["unique_fraction"] < MIN_UNIQUE_FRACTION:
            failures.append(
                f"{band}: unique-input fraction below {MIN_UNIQUE_FRACTION:.0%}"
            )

    return {
        "schema": "d5d9fdb01bdd-lesson-probe-v1",
        "task_id": TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": _digest(GENERATOR_PATH),
        "rule_hash": gen.RULE_HASH,
        "windows_per_band": windows_per_band,
        "minimum_unique_fraction": MIN_UNIQUE_FRACTION,
        "lesson_size": gen.EXAMPLES_NEEDED + 1,
        "query_rotations_per_lesson": gen.EXAMPLES_NEEDED + 1,
        "schedule_profiles": list(gen.SCHEDULE_PROFILES),
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "competitors": sorted(competitors),
        "witnesses": sorted(witnesses),
        "bands": bands,
        "joint_boundary_overrides": joint_overrides,
        "unique_inputs_total": len(all_unique),
        "first_counterexample_per_competitor": counterexamples,
        "limitations": [
            "Checks only declared rivals plus exact joint boundary controls.",
            "Duplicates across independent lessons are reported; at least 85% unique inputs is required.",
            "Finite generated lessons do not prove universal identifiability.",
            "Python rule_mirror is trusted only after an external Racket rule-smoke pass.",
        ],
        "failures": failures,
        "passed": not failures,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--windows-per-band", type=int, default=100)
    parser.add_argument("--seed", type=int, default=515_000)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    report = build_report(
        windows_per_band=args.windows_per_band,
        seed=args.seed,
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(payload)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
