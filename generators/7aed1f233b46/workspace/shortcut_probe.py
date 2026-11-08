#!/usr/bin/env python3
"""Census generated examples for semantic drift and shortcut survivorship.

This stays source-bound to 7aed1f233b46 but is intentionally reusable by future
reviewers: it reports grammar failures, canonical input profiles, scheduled
profile coverage, output-shape coverage, per-rival counterexamples, and any
sliding demonstration window in which a named rival still fits every example.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parent.parent
REPO_ROOT = HERE.parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = TASK_DIR / "generator.py"
    name = "shortcut_probe_7aed1f233b46_generator"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _shape(grid: list[list[int]]) -> str:
    return f"{len(grid)}x{len(grid[0])}"


def run_census(
    *,
    seed: int = 0,
    samples: int = 25,
    difficulty: str = "hard",
) -> dict[str, Any]:
    """Return a deterministic JSON-serializable semantic census."""
    if samples < 1:
        raise ValueError("samples must be positive")

    gen = _load_generator()
    profile_counts: Counter[str] = Counter()
    input_profile_counts: Counter[str] = Counter()
    output_shape_counts: Counter[str] = Counter()
    shortcut_witness_counts: Counter[str] = Counter(
        {name: 0 for name in gen.SEMANTIC_RIVALS}
    )
    generation_failures: list[dict[str, Any]] = []
    examples: list[dict[str, Any]] = []

    for sample_index in range(samples):
        try:
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            self_errors = list(gen.self_check(grid))
            strict_errors = list(gen.strict_canonical_like(grid))
            if self_errors or strict_errors:
                generation_failures.append(
                    {
                        "sample_index": sample_index,
                        "self_check": self_errors,
                        "strict_canonical_like": strict_errors,
                    }
                )
                continue

            facts = gen.semantic_observables(grid)
            truth = gen.rule_mirror(grid)
            profile_counts[facts["scene_profile"]] += 1
            input_profile_counts[
                f"{facts['height']}x{facts['width']}/{len(facts['palette']) + 1}colors"
            ] += 1
            output_shape_counts[_shape(truth)] += 1

            rival_outputs: dict[str, list[list[int]]] = {}
            for name, rival in gen.SEMANTIC_RIVALS.items():
                rival_output = rival(grid)
                rival_outputs[name] = rival_output
                if rival_output != truth:
                    shortcut_witness_counts[name] += 1
            examples.append(
                {
                    "sample_index": sample_index,
                    "input": grid,
                    "output": truth,
                    "rival_outputs": rival_outputs,
                }
            )
        except Exception as exc:  # diagnostic tool: retain all sample failures
            generation_failures.append(
                {
                    "sample_index": sample_index,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            )

    window_size = int(gen.EXAMPLES_NEEDED)
    surviving_lesson_rivals: dict[str, list[int]] = {}
    for start in range(max(0, len(examples) - window_size + 1)):
        window = examples[start : start + window_size]
        for name in gen.SEMANTIC_RIVALS:
            if all(example["rival_outputs"][name] == example["output"] for example in window):
                surviving_lesson_rivals.setdefault(name, []).append(start)

    return {
        "task_id": gen.TASK_ID,
        "version": gen.VERSION,
        "seed": seed,
        "samples_requested": samples,
        "samples_checked": len(examples),
        "difficulty": difficulty,
        "lesson_window_size": window_size,
        "profile_counts": dict(sorted(profile_counts.items())),
        "input_profile_counts": dict(sorted(input_profile_counts.items())),
        "output_shape_counts": dict(sorted(output_shape_counts.items())),
        "distinct_output_shapes": len(output_shape_counts),
        "shortcut_witness_counts": dict(sorted(shortcut_witness_counts.items())),
        "surviving_lesson_rivals": surviving_lesson_rivals,
        "generation_failures": generation_failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--samples", type=int, default=25)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="hard")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit nonzero on invalid samples, surviving rivals, or an unwitnessed rival",
    )
    args = parser.parse_args()
    report = run_census(seed=args.seed, samples=args.samples, difficulty=args.difficulty)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not args.strict:
        return 0
    unwitnessed = [
        name for name, count in report["shortcut_witness_counts"].items() if count == 0
    ]
    return int(
        bool(report["generation_failures"])
        or bool(report["surviving_lesson_rivals"])
        or bool(unwitnessed)
    )


if __name__ == "__main__":
    raise SystemExit(main())
