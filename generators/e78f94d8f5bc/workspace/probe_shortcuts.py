#!/usr/bin/env python3
"""Measure endpoint/lattice shortcuts for the e78f94d8f5bc generator.

The probe is source-bound: pass any generator.py (for example the immutable
baseline or the repaired file) and it records the source hash plus exact witness
grids.  It intentionally uses only public generation/rule functions and simple
grid predicates so future reviewers can replay it without the check harness.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path
import sys
from typing import Any

TASK_ID = "e78f94d8f5bc"
BANDS = ("easy", "medium", "hard")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_generator(path: Path):
    runtime = _repo_root() / "shared" / "runtime"
    sys.path.insert(0, str(runtime))
    module_name = f"shortcut_probe_{hashlib.sha256(path.read_bytes()).hexdigest()[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _endpoints(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]


def _all_endpoints_even_even(grid: list[list[int]]) -> bool:
    points = _endpoints(grid)
    return len(points) == 2 and all(r % 2 == 0 and c % 2 == 0 for r, c in points)


def _all_endpoints_on_boundary(grid: list[list[int]]) -> bool:
    h, w = len(grid), len(grid[0])
    points = _endpoints(grid)
    return len(points) == 2 and all(
        r in (0, h - 1) or c in (0, w - 1) for r, c in points
    )


def _all_odd_odd_are_walls(grid: list[list[int]]) -> bool:
    return all(
        grid[r][c] == 1
        for r in range(1, len(grid), 2)
        for c in range(1, len(grid[0]), 2)
    )


def _parity_pattern(grid: list[list[int]]) -> str:
    return "/".join(f"{r % 2}{c % 2}" for r, c in sorted(_endpoints(grid)))


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _anchored_lattice_rival(generator, grid: list[list[int]]) -> list[list[int]]:
    if _all_endpoints_even_even(grid) and _all_odd_odd_are_walls(grid):
        return generator.rule_mirror(grid)
    return _identity(grid)


def _boundary_only_rival(generator, grid: list[list[int]]) -> list[list[int]]:
    if _all_endpoints_on_boundary(grid):
        return generator.rule_mirror(grid)
    return _identity(grid)


def _load_canonical(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise RuntimeError(f"canonical task {TASK_ID} not found in {path}")


def _witness(generator, grid: list[list[int]], rival) -> dict[str, Any]:
    truth = generator.rule_mirror(grid)
    rival_output = rival(generator, grid)
    return {
        "input": grid,
        "endpoints": _endpoints(grid),
        "intended_output": truth,
        "rival_output": rival_output,
        "rival_disagrees": rival_output != truth,
    }


def run(generator_path: Path, samples_per_band: int, seed: int) -> dict[str, Any]:
    generator_path = generator_path.resolve()
    generator = _load_generator(generator_path)
    canonical_path = _repo_root() / "shared" / "data" / "canonical" / "puzzles.jsonl"
    canonical = _load_canonical(canonical_path)

    parity_counts: Counter[str] = Counter()
    total = 0
    anchored_endpoint_count = 0
    odd_odd_wall_count = 0
    all_boundary_count = 0
    lattice_witness = None
    interior_endpoint_witness = None

    for difficulty in BANDS:
        for sample_index in range(samples_per_band):
            grid = generator.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                grid_h=6,
                grid_w=6,
                route_turns=3,
            )
            errors = generator.self_check(grid)
            if errors:
                raise AssertionError(
                    f"unlawful sample {difficulty}/{sample_index}: {'; '.join(errors)}"
                )
            total += 1
            parity_counts[_parity_pattern(grid)] += 1
            anchored = _all_endpoints_even_even(grid)
            odd_odd = _all_odd_odd_are_walls(grid)
            boundary = _all_endpoints_on_boundary(grid)
            anchored_endpoint_count += int(anchored)
            odd_odd_wall_count += int(odd_odd)
            all_boundary_count += int(boundary)
            if lattice_witness is None and not (anchored and odd_odd):
                lattice_witness = {
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    **_witness(generator, grid, _anchored_lattice_rival),
                }
            if interior_endpoint_witness is None and not boundary:
                interior_endpoint_witness = {
                    "difficulty": difficulty,
                    "sample_index": sample_index,
                    **_witness(generator, grid, _boundary_only_rival),
                }

    train = canonical.get("train", [])
    canonical_checks = []
    for index, pair in enumerate(train):
        grid = pair["input"]
        truth = pair["output"]
        mirrored = generator.rule_mirror(grid)
        canonical_checks.append(
            {
                "index": index,
                "mirror_matches": mirrored == truth,
                "all_endpoints_on_boundary": _all_endpoints_on_boundary(grid),
                "boundary_rival_matches": _boundary_only_rival(generator, grid) == truth,
                "anchored_lattice_rival_matches": _anchored_lattice_rival(generator, grid)
                == truth,
            }
        )

    return {
        "schema": "e78f94d8f5bc-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(generator_path.read_bytes()).hexdigest(),
        "generator_version": getattr(generator, "VERSION", None),
        "seed": seed,
        "samples_per_band": samples_per_band,
        "bands": list(BANDS),
        "total_samples": total,
        "fixed_6x6_route_turns": 3,
        "endpoint_parity_patterns": dict(sorted(parity_counts.items())),
        "all_endpoints_even_even": {
            "count": anchored_endpoint_count,
            "fraction": anchored_endpoint_count / total,
        },
        "all_odd_odd_are_walls": {
            "count": odd_odd_wall_count,
            "fraction": odd_odd_wall_count / total,
        },
        "all_endpoints_on_boundary": {
            "count": all_boundary_count,
            "fraction": all_boundary_count / total,
        },
        "canonical_train_checks": canonical_checks,
        "canonical_boundary_rival_fit_count": sum(
            item["boundary_rival_matches"] for item in canonical_checks
        ),
        "canonical_anchored_lattice_rival_fit_count": sum(
            item["anchored_lattice_rival_matches"] for item in canonical_checks
        ),
        "lattice_phase_counterexample": lattice_witness,
        "interior_endpoint_counterexample": interior_endpoint_witness,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--samples-per-band", type=int, default=600)
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.samples_per_band < 1:
        parser.error("--samples-per-band must be positive")
    result = run(args.generator, args.samples_per_band, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "out": str(args.out),
        "generator_sha256": result["generator_sha256"],
        "total_samples": result["total_samples"],
        "endpoint_parity_patterns": result["endpoint_parity_patterns"],
        "all_endpoints_even_even": result["all_endpoints_even_even"],
        "all_odd_odd_are_walls": result["all_odd_odd_are_walls"],
        "canonical_boundary_rival_fit_count": result["canonical_boundary_rival_fit_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
