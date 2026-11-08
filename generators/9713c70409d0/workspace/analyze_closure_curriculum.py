#!/usr/bin/env python3
"""Measure semantic coverage of the 9713c70409d0 generator curriculum.

Run from a prepared ARCpuzzles runtime, for example:

    PYTHONPATH=/path/to/runtime python analyze_closure_curriculum.py --samples-per-band 40

The report is intentionally task-local: it measures declared profiles, strict
canonical support, output diversity, witness coverage, and named-rival
counterexamples without executing or approximating the Racket authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib
import json
from pathlib import Path
from typing import Any

TASK_ID = "9713c70409d0"
BANDS = ("easy", "medium", "hard")


def _frozen_grid(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def _edge_count(matrix: list[list[int]]) -> int:
    return sum(
        matrix[i][j] == 8
        for i in range(len(matrix))
        for j in range(i + 1, len(matrix))
    )


def analyze(generator, *, samples_per_band: int = 40, base_seed: int = 0) -> dict[str, Any]:
    """Return a deterministic JSON-serializable curriculum coverage report."""
    if type(samples_per_band) is not int or samples_per_band < 1:
        raise ValueError("samples_per_band must be a positive integer")
    if type(base_seed) is not int:
        raise ValueError("base_seed must be an integer")

    profiles: Counter[str] = Counter()
    output_shapes: Counter[str] = Counter()
    edge_histogram: Counter[str] = Counter()
    witness_firings: Counter[str] = Counter(
        {name: 0 for name in generator.SEMANTIC_WITNESSES}
    )
    rival_disagreements: Counter[str] = Counter(
        {name: 0 for name in generator.SEMANTIC_RIVALS}
    )
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    unique_outputs: set[tuple[tuple[int, ...], ...]] = set()
    invalid_draws: list[dict[str, Any]] = []
    strict = 0
    total = 0

    for band_index, difficulty in enumerate(BANDS):
        for sample_index in range(samples_per_band):
            seed = base_seed + band_index * 1_000_003 + sample_index
            try:
                grid = generator.generate(seed, sample_index, difficulty=difficulty)
                errors = list(generator.self_check(grid))
            except Exception as exc:  # counted and serialized, never hidden
                invalid_draws.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "seed": seed,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                continue
            if errors:
                invalid_draws.append(
                    {
                        "difficulty": difficulty,
                        "sample_index": sample_index,
                        "seed": seed,
                        "error": "; ".join(errors),
                    }
                )
                continue

            profile = generator.observe_overrides(grid)["scene_profile"]
            output = generator.rule_mirror(grid)
            profiles[profile] += 1
            strict += not generator.strict_canonical_like(grid)
            total += 1
            unique_inputs.add(_frozen_grid(grid))
            unique_outputs.add(_frozen_grid(output))
            output_shapes[f"{len(output)}x{len(output[0])}"] += 1
            edge_histogram[str(_edge_count(output))] += 1

            for name, witness in generator.SEMANTIC_WITNESSES.items():
                witness_firings[name] += bool(witness(grid))
            for name, rival in generator.SEMANTIC_RIVALS.items():
                rival_disagreements[name] += rival(grid) != output

    return {
        "schema": "closure-curriculum-analysis/1",
        "task_id": generator.TASK_ID,
        "generator_version": generator.VERSION,
        "samples_per_band": samples_per_band,
        "base_seed": base_seed,
        "draws_requested": samples_per_band * len(BANDS),
        "draws_valid": total,
        "invalid_draws": invalid_draws,
        "profiles": dict(sorted(profiles.items())),
        "strict_fraction": strict / total if total else 0.0,
        "unique_inputs": len(unique_inputs),
        "unique_outputs": len(unique_outputs),
        "output_shapes": dict(sorted(output_shapes.items())),
        "relation_edge_histogram": dict(
            sorted(edge_histogram.items(), key=lambda item: int(item[0]))
        ),
        "witness_firings": dict(sorted(witness_firings.items())),
        "rival_disagreements": dict(sorted(rival_disagreements.items())),
    }


def _load_generator():
    return importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-band", type=int, default=40)
    parser.add_argument("--base-seed", type=int, default=0)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args(argv)

    report = analyze(
        _load_generator(),
        samples_per_band=args.samples_per_band,
        base_seed=args.base_seed,
    )
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if report["invalid_draws"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
