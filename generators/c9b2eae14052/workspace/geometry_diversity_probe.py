#!/usr/bin/env python3
"""Measure color-independent geometry diversity for one ARC generator.

This catches palette-only diversity: many distinct colored grids backed by the
same tiny set of object layouts.  The output pins the generator SHA, seed range,
schedule profiles, public axes, and exact unique-signature counts.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_ROOT.parents[1]
RUNTIME = REPO_ROOT / "shared" / "runtime"


def _load_generator(path: Path):
    sys.path.insert(0, str(RUNTIME))
    spec = importlib.util.spec_from_file_location(
        f"geometry_probe_{hashlib.sha256(str(path).encode()).hexdigest()[:12]}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _grid_signature(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value != 0) for value in row) for row in grid)


def _shape_signature(gen: Any, grid: list[list[int]]) -> tuple[Any, ...]:
    records = gen._analysis(grid)["records"]
    result = []
    for record in records:
        cells = record["cells"]
        min_r = min(r for r, _c in cells)
        min_c = min(c for _r, c in cells)
        normalized = tuple(sorted((r - min_r, c - min_c) for r, c in cells))
        result.append((record["border_count"], tuple(sorted(record["sides"])), normalized))
    return tuple(sorted(result))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, default=TASK_ROOT / "generator.py")
    parser.add_argument("--seed-start", type=int, default=12_000)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--profiles", type=int, default=12)
    parser.add_argument("--min-unique", type=int, default=0)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    path = args.generator.resolve()
    source = path.read_bytes()
    gen = _load_generator(path)
    rows = []
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(args.profiles):
            grids = [
                gen.generate(seed, sample_index, difficulty=difficulty)
                for seed in range(args.seed_start, args.seed_start + args.seeds)
            ]
            outputs = [gen.rule_mirror(grid) for grid in grids]
            axes = [gen.observe_overrides(grid) for grid in grids]
            rows.append(
                {
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    "draws": len(grids),
                    "axes": axes[0],
                    "axes_constant": all(axis == axes[0] for axis in axes),
                    "unique_input_binary_layouts": len({_grid_signature(grid) for grid in grids}),
                    "unique_output_binary_layouts": len({_grid_signature(grid) for grid in outputs}),
                    "unique_component_shape_multisets": len(
                        {_shape_signature(gen, grid) for grid in grids}
                    ),
                }
            )

    counts = [row["unique_input_binary_layouts"] for row in rows]
    report = {
        "schema": "c9b2eae14052-geometry-diversity-v1",
        "generator_path": str(path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "version": getattr(gen, "VERSION", None),
        "seed_start": args.seed_start,
        "seed_stop_exclusive": args.seed_start + args.seeds,
        "seeds_per_profile": args.seeds,
        "profile_count_per_band": args.profiles,
        "bands": ["easy", "medium", "hard"],
        "total_draws": len(rows) * args.seeds,
        "minimum_unique_input_binary_layouts": min(counts),
        "median_unique_input_binary_layouts": statistics.median(counts),
        "maximum_unique_input_binary_layouts": max(counts),
        "required_minimum": args.min_unique,
        "passed": min(counts) >= args.min_unique,
        "profiles": rows,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
