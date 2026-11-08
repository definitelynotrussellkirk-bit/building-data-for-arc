#!/usr/bin/env python3
"""Exhaustive small-period curriculum probe for generator 0e4adc584fa1.

This is task-local reviewer tooling.  It binds to the generator next to this
workspace, checks exact observable controls, all consecutive starts in a chosen
period, every possible query rotation, and the generator's *declared* rivals
and canonical shortcuts.  It does not claim uniqueness outside that finite
rival class.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import canonical_pairs, find_root


def load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("reviewed_generator_0e4adc584fa1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def pair(gen, grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def check_exact_overrides(gen) -> list[dict[str, Any]]:
    cases = [
        {"grid_h": value} for value in (8, 12)
    ] + [
        {"grid_w": value} for value in (9, 14)
    ] + [
        {"control_code": value} for value in (1, 2, 3, 4)
    ] + [
        {"shape_profile": value} for value in gen.SHAPE_PROFILES
    ] + [
        {"shape_colors": value} for value in (1, 2, 3)
    ] + [
        {"marker_order": value} for value in gen.MARKER_ORDERS
    ]
    failures = []
    for index, overrides in enumerate(cases):
        grid = gen.generate(9001 + index, index, difficulty="medium", **overrides)
        observed = gen.observe_overrides(grid)
        mismatch = {name: {"requested": value, "observed": observed.get(name)}
                    for name, value in overrides.items() if observed.get(name) != value}
        if mismatch:
            failures.append({"case": index, "overrides": overrides, "mismatch": mismatch})
    return failures


def run(period: int, seeds: int) -> dict[str, Any]:
    gen, generator_path = load_generator()
    root = find_root(generator_path)
    canonical = canonical_pairs(gen.TASK_ID, root=root)
    canonical_shortcuts = dict(getattr(gen, "CANONICAL_SHORTCUTS", {}))
    competitors = dict(getattr(gen, "LESSON_COMPETITORS", {}))

    canonical_fit = {}
    for name, rival in sorted(canonical_shortcuts.items()):
        fits = sum(rival(item["input"]) == item["output"] for item in canonical)
        canonical_fit[name] = {"fits": fits, "pairs": len(canonical)}

    windows = 0
    rotations = 0
    failures: list[dict[str, Any]] = []
    min_demo_codes = 99
    competitor_refutations = {name: 0 for name in competitors}
    shortcut_refutations = {name: 0 for name in canonical_shortcuts}
    unique_inputs: set[str] = set()

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(seeds):
            for start in range(period):
                grids = [gen.generate(seed, start + offset, difficulty=difficulty)
                         for offset in range(5)]
                pairs = [pair(gen, grid) for grid in grids]
                windows += 1
                codes = [gen.observe_overrides(grid)["control_code"] for grid in grids]
                if set(codes[:4]) != {1, 2, 3, 4}:
                    failures.append({"kind": "default_four_code_coverage", "difficulty": difficulty,
                                     "seed": seed, "start": start, "codes": codes})
                for grid in grids:
                    unique_inputs.add(hashlib.sha256(
                        json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

                for name, rival in competitors.items():
                    if any(rival(item["input"]) != item["output"] for item in pairs[:4]):
                        competitor_refutations[name] += 1
                for name, rival in canonical_shortcuts.items():
                    if any(rival(item["input"]) != item["output"] for item in pairs[:4]):
                        shortcut_refutations[name] += 1

                for query_index in range(5):
                    demos = [item for index, item in enumerate(pairs) if index != query_index]
                    query = pairs[query_index]
                    demo_codes = {gen.observe_overrides(item["input"])["control_code"] for item in demos}
                    min_demo_codes = min(min_demo_codes, len(demo_codes))
                    errors = gen.lesson_identifiable(demos, query)
                    rotations += 1
                    if errors:
                        failures.append({"kind": "ambiguous_rotation", "difficulty": difficulty,
                                         "seed": seed, "start": start,
                                         "query_index": query_index, "errors": errors})

    override_failures = check_exact_overrides(gen)
    failures.extend({"kind": "override", **row} for row in override_failures)
    for name, result in canonical_fit.items():
        if result["fits"] != result["pairs"]:
            failures.append({"kind": "declared_shortcut_does_not_fit_canonical", "name": name, **result})
    for name, count in shortcut_refutations.items():
        if count != windows:
            failures.append({"kind": "shortcut_not_refuted_in_every_default_lesson", "name": name,
                             "refuted_windows": count, "windows": windows})

    return {
        "schema": "0e4adc584fa1-curriculum-probe-v1",
        "task_id": gen.TASK_ID,
        "generator_version": gen.VERSION,
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "settings": {"period": period, "seeds": seeds,
                     "difficulties": ["easy", "medium", "hard"],
                     "pairs_per_window": 5, "query_rotations_per_window": 5},
        "counts": {"windows": windows, "rotations": rotations,
                   "unique_inputs": len(unique_inputs),
                   "exact_override_cases": 2 + 2 + 4 + len(gen.SHAPE_PROFILES) + 3 + len(gen.MARKER_ORDERS)},
        "minimum_distinct_demo_codes_across_rotations": min_demo_codes,
        "canonical_pairs": len(canonical),
        "canonical_shortcut_fit": canonical_fit,
        "competitor_refuted_by_default_four_demos": competitor_refutations,
        "canonical_shortcut_refuted_by_default_four_demos": shortcut_refutations,
        "failures": failures,
        "passed": not failures,
        "limits": [
            "Finite declared-rival check, not a proof of universal identifiability.",
            "Enumerates consecutive starts only within the requested period and seed range.",
            "Uses the Python rule mirror for labels; the required battery separately binds it to Racket authority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", type=int, default=20)
    parser.add_argument("--seeds", type=int, default=8)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.period < 1 or args.seeds < 1:
        parser.error("--period and --seeds must be positive")
    report = run(args.period, args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
