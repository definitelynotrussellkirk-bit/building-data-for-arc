#!/usr/bin/env python3
"""Reproducible distribution/contract stress probe for aa378df15340.

This is reviewer tooling.  It uses the independent helpers in reference_probe.py
and writes a compact JSON receipt rather than relying on console assertions.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any

from reference_probe import load_generator, observed, teaching_errors

BANDS: tuple[str | None, ...] = (None, "easy", "medium", "hard")


def frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def source_hash(module: Any) -> str:
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def run(per_band: int) -> dict[str, Any]:
    gen = load_generator()
    failures: list[dict[str, Any]] = []
    bands: dict[str, Any] = {}
    all_inputs: set[tuple[tuple[int, ...], ...]] = set()

    for band_index, band in enumerate(BANDS):
        key = "default" if band is None else band
        counts = {name: Counter() for name in ("grid_n", "n_seeds", "n_colors")}
        local_inputs: set[tuple[tuple[int, ...], ...]] = set()
        for i in range(per_band):
            seed = 310_000 + band_index * 100_000 + i
            sample_index = i * 37 + band_index
            grid = gen.generate(seed, sample_index, difficulty=band)
            replay = gen.generate(seed, sample_index, difficulty=band)
            problems = list(gen.self_check(grid, difficulty=band)) + teaching_errors(grid)
            if replay != grid:
                problems.append("nondeterministic replay")
            coords = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
            if any(grid[c][r] != 0 for r, c in coords):
                problems.append("occupied transpose target")
            if problems:
                failures.append({
                    "band": key,
                    "seed": seed,
                    "sample_index": sample_index,
                    "problems": problems,
                })
                if len(failures) >= 20:
                    break
            stats = observed(grid)
            for name, value in stats.items():
                counts[name][str(value)] += 1
            item = frozen(grid)
            local_inputs.add(item)
            all_inputs.add(item)
        bands[key] = {
            "draws": per_band,
            "unique_inputs": len(local_inputs),
            "histograms": {name: dict(sorted(counter.items(), key=lambda kv: int(kv[0])))
                           for name, counter in counts.items()},
        }

    exact_override_cases = 0
    for band in BANDS:
        for grid_n in range(5, 13):
            for n_seeds in range(3, 10):
                for n_colors in range(1, min(4, n_seeds) + 1):
                    requested = {
                        "grid_n": grid_n,
                        "n_seeds": n_seeds,
                        "n_colors": n_colors,
                    }
                    grid = gen.generate(
                        920_000 + exact_override_cases,
                        exact_override_cases,
                        difficulty=band,
                        **requested,
                    )
                    actual = gen.observe_overrides(grid)
                    problems = list(gen.self_check(
                        grid,
                        difficulty=band,
                        meta={"overrides": requested},
                    )) + teaching_errors(grid)
                    if actual != requested:
                        problems.append(f"override mismatch: requested={requested}, actual={actual}")
                    if problems:
                        failures.append({
                            "band": "default" if band is None else band,
                            "exact_overrides": requested,
                            "problems": problems,
                        })
                    exact_override_cases += 1

    result = {
        "schema": "aa378df15340_stress_probe/1",
        "generator_sha256": source_hash(gen),
        "per_band": per_band,
        "total_default_draws": per_band * len(BANDS),
        "total_unique_default_inputs": len(all_inputs),
        "exact_override_cases": exact_override_cases,
        "bands": bands,
        "failure_count": len(failures),
        "failures": failures,
        "verdict": "pass" if not failures else "fail",
        "limits": [
            "Finite deterministic sample; not an exhaustive proof over all seeds.",
            "Semantic comparison covers the declared upper-triangle-only rival.",
        ],
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-band", type=int, default=1000)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    result = run(args.per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "verdict": result["verdict"],
        "failure_count": result["failure_count"],
        "total_default_draws": result["total_default_draws"],
        "exact_override_cases": result["exact_override_cases"],
        "generator_sha256": result["generator_sha256"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
