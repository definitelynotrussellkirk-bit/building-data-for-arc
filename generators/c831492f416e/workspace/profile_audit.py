#!/usr/bin/env python3
"""Task-local semantic census for ``c831492f416e``.

This read-only tool checks the parts of the curriculum that marginal morphology
metrics cannot see: exact profile observability, canonical mirror parity,
strict-manifold rate, endpoint safety, complete five-example lessons, and
explicit rival refutation. It is intentionally independent of the shared
battery so a future editor can run one cheap command immediately after a
change.
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
REPO = Path(__file__).resolve().parents[3]


def _freeze(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _norm_grid(grid):
    if isinstance(grid, list) and grid and all(isinstance(row, str) for row in grid):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def _canonical_pairs(task_id: str) -> list[dict[str, list[list[int]]]]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != task_id:
            continue
        raw_pairs = list(row.get("train", []))
        raw_test = row.get("test", [])
        raw_pairs.extend(raw_test if isinstance(raw_test, list) else [raw_test])
        return [
            {
                "input": _norm_grid(pair["input"]),
                "output": _norm_grid(pair["output"]),
            }
            for pair in raw_pairs
        ]
    raise RuntimeError(f"canonical task {task_id!r} not found in {path}")


def audit_census(generator: ModuleType, *, seeds: int = 25) -> dict[str, Any]:
    if isinstance(seeds, bool) or not isinstance(seeds, int) or seeds < 1:
        raise ValueError("seeds must be a positive integer")

    canonical_mismatches: list[dict[str, Any]] = []
    for index, pair in enumerate(_canonical_pairs(generator.TASK_ID)):
        actual = generator.rule_mirror(pair["input"])
        if actual != pair["output"]:
            canonical_mismatches.append({
                "pair_index": index,
                "expected": pair["output"],
                "actual": actual,
            })

    profile_counts: Counter[str] = Counter()
    signature_counts: Counter[str] = Counter()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    unique_outputs: set[tuple[tuple[int, ...], ...]] = set()
    self_check_failures: list[dict[str, Any]] = []
    observer_mismatches: list[dict[str, Any]] = []
    endpoint_risks: list[dict[str, Any]] = []
    lesson_failures: list[dict[str, Any]] = []
    surviving_rivals: list[dict[str, Any]] = []
    strict_hits = 0
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
                observed = generator.observe_overrides(grid).get("scene_profile")
                if observed is not None:
                    profile_counts[observed] += 1
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
                strict_hits += int(not generator.strict_canonical_like(grid))
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
            for name, rival in generator.LESSON_COMPETITORS.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    surviving_rivals.append({
                        "band": band,
                        "seed": seed,
                        "rival": name,
                    })

    strict_rate = strict_hits / draws if draws else 0.0
    passed = not (
        canonical_mismatches
        or self_check_failures
        or observer_mismatches
        or endpoint_risks
        or lesson_failures
        or surviving_rivals
    ) and strict_rate >= float(generator.MIN_STRICT_FRAC)

    return {
        "task_id": generator.TASK_ID,
        "version": generator.VERSION,
        "rule_hash": generator.RULE_HASH,
        "seeds": seeds,
        "bands": list(BANDS),
        "draws": draws,
        "unique_inputs": len(unique_inputs),
        "unique_outputs": len(unique_outputs),
        "profile_counts": {
            profile: profile_counts[profile] for profile in generator.SCENE_PROFILES
        },
        "signature_counts": dict(sorted(signature_counts.items())),
        "strict_hits": strict_hits,
        "strict_rate": strict_rate,
        "min_strict_frac": generator.MIN_STRICT_FRAC,
        "canonical_mismatches": canonical_mismatches,
        "self_check_failures": self_check_failures,
        "observer_mismatches": observer_mismatches,
        "endpoint_overwrite_risks": endpoint_risks,
        "lesson_failures": lesson_failures,
        "surviving_rivals": surviving_rivals,
        "passed": passed,
    }


def _load_sibling_generator() -> ModuleType:
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("c831492f416e_generator", path)
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
