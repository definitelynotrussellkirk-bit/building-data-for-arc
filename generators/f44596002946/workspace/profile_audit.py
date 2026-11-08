#!/usr/bin/env python3
"""Task-local semantic census for ``f44596002946``.

This is intentionally independent of the shared review battery.  It gives the
next generator author one cheap command that verifies scheduled profile
coverage, public-axis observability, endpoint safety, canonical signatures, and
whole-lesson rival refutation after any edit.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

BANDS = ("easy", "medium", "hard")


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def audit_census(generator: ModuleType, *, seeds: int = 25) -> dict[str, Any]:
    if isinstance(seeds, bool) or not isinstance(seeds, int) or seeds < 1:
        raise ValueError("seeds must be a positive integer")

    profile_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    unique_outputs: set[tuple[tuple[int, ...], ...]] = set()
    self_check_failures: list[dict[str, Any]] = []
    observer_mismatches: list[dict[str, Any]] = []
    endpoint_risks: list[dict[str, Any]] = []
    lesson_failures: list[dict[str, Any]] = []
    draws = 0

    for band in BANDS:
        for seed in range(seeds):
            demos = []
            for sample_index, expected_profile in enumerate(generator.SCENE_PROFILES):
                grid = generator.generate(seed, sample_index, difficulty=band)
                output = generator.rule_mirror(grid)
                draws += 1
                unique_inputs.add(_freeze(grid))
                unique_outputs.add(_freeze(output))
                profile_counts[expected_profile] += 1
                signature = (
                    len(grid),
                    len(grid[0]),
                    len({value for row in grid for value in row}),
                )
                signature_counts["x".join(map(str, signature))] += 1

                errors = generator.self_check(grid, difficulty=band)
                if errors:
                    self_check_failures.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "errors": list(errors),
                    })
                observed = generator.observe_overrides(grid).get("scene_profile")
                if observed != expected_profile:
                    observer_mismatches.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                        "expected": expected_profile,
                        "observed": observed,
                    })
                analysis = generator.analyze_grid(grid)
                if analysis.get("endpoint_overwrite_risk"):
                    endpoint_risks.append({
                        "band": band,
                        "seed": seed,
                        "sample_index": sample_index,
                    })
                demos.append({"input": grid, "output": output})

            query_input = generator.generate(
                seed, generator.EXAMPLES_NEEDED, difficulty=band
            )
            query = {
                "input": query_input,
                "output": generator.rule_mirror(query_input),
            }
            reasons = generator.lesson_identifiable(demos, query)
            if reasons:
                lesson_failures.append({
                    "band": band,
                    "seed": seed,
                    "reasons": list(reasons),
                })

    return {
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "seeds": seeds,
        "bands": list(BANDS),
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "unique_outputs": len(unique_outputs),
        "profile_counts": {
            profile: profile_counts[profile] for profile in generator.SCENE_PROFILES
        },
        "signature_counts": dict(sorted(signature_counts.items())),
        "self_check_failures": self_check_failures,
        "observer_mismatches": observer_mismatches,
        "endpoint_overwrite_risks": endpoint_risks,
        "lesson_failures": lesson_failures,
        "passed": not (
            self_check_failures
            or observer_mismatches
            or endpoint_risks
            or lesson_failures
        ),
    }


def _load_sibling_generator() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("f44596002946_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=25)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = audit_census(_load_sibling_generator(), seeds=args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
