#!/usr/bin/env python3
"""Independent reference probe for generator 60a8a9d74a75.

The probe deliberately reimplements the zero-component rule instead of calling
``generator.rule_mirror``.  It can inspect one generated sample or scan a run of
samples, report region semantics, and compare every rival declared by the
current generator.  Run from the repository root, for example::

    python3 generators/60a8a9d74a75/workspace/reference_probe.py \
        --seed 901 --sample-index 1 --difficulty hard \
        --profile composite_open_left --out /tmp/probe.json
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence

Grid = list[list[int]]
Cell = tuple[int, int]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_grid(grid: Sequence[Sequence[int]]) -> None:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a nonempty list or tuple")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("grid rows must be nonempty lists or tuples")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer ARC colours 0..9")


def zero_regions(grid: Sequence[Sequence[int]]) -> list[dict[str, Any]]:
    """Return an independently computed description of every 4-connected zero region."""
    _validate_grid(grid)
    h, w = len(grid), len(grid[0])
    unseen: set[Cell] = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 0
    }
    regions: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in _CARDINAL:
                point = (r + dr, c + dc)
                if point in unseen:
                    unseen.remove(point)
                    cells.add(point)
                    queue.append(point)

        neighbor_values: dict[Cell, int] = {}
        wall_cells: set[Cell] = set()
        edge_sides: set[str] = set()
        for r, c in cells:
            if r == 0:
                edge_sides.add("top")
            if r == h - 1:
                edge_sides.add("bottom")
            if c == 0:
                edge_sides.add("left")
            if c == w - 1:
                edge_sides.add("right")
            for dr, dc in _CARDINAL:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < h and 0 <= nc < w):
                    continue
                value = grid[nr][nc]
                if value == 8:
                    wall_cells.add((nr, nc))
                elif value != 0:
                    neighbor_values[(nr, nc)] = value

        colors = sorted(set(neighbor_values.values()))
        regions.append(
            {
                "cells": cells,
                "edge_sides": edge_sides,
                "neighbor_values": neighbor_values,
                "wall_cells": wall_cells,
                "colors": colors,
            }
        )
    return regions


def reference_rule(grid: Sequence[Sequence[int]]) -> Grid:
    """Apply the intended rule without importing production implementation code."""
    _validate_grid(grid)
    out: Grid = deepcopy([list(row) for row in grid])
    for region in zero_regions(grid):
        colors = region["colors"]
        if len(colors) == 1:
            color = colors[0]
            for r, c in region["cells"]:
                out[r][c] = color
    return out


def _grid_sha256(grid: Sequence[Sequence[int]]) -> str:
    payload = json.dumps(grid, separators=(",", ":"), sort_keys=False).encode()
    return hashlib.sha256(payload).hexdigest()


def analyze_grid(
    grid: Sequence[Sequence[int]],
    *,
    rivals: Mapping[str, Callable[[Grid], Grid]] | None = None,
) -> dict[str, Any]:
    """Describe one grid, its independent label, and optional rival predictions."""
    canonical_grid: Grid = [list(row) for row in grid]
    regions = zero_regions(canonical_grid)
    truth = reference_rule(canonical_grid)
    region_rows = []
    for index, region in enumerate(regions):
        colors = list(region["colors"])
        region_rows.append(
            {
                "index": index,
                "size": len(region["cells"]),
                "touches_edge": bool(region["edge_sides"]),
                "edge_sides": sorted(region["edge_sides"]),
                "neighbor_cell_count": len(region["neighbor_values"]),
                "neighbor_colors": colors,
                "wall_cell_count": len(region["wall_cells"]),
                "filled_by_reference": len(colors) == 1,
                "reference_fill_color": colors[0] if len(colors) == 1 else None,
                "cells": [list(point) for point in sorted(region["cells"])],
            }
        )

    rival_rows: dict[str, dict[str, Any]] = {}
    for name, rival in sorted((rivals or {}).items()):
        prediction = rival(deepcopy(canonical_grid))
        rival_rows[name] = {
            "disagrees": prediction != truth,
            "output_sha256": _grid_sha256(prediction),
            "output": prediction,
        }

    changed = sum(
        before != after
        for before_row, after_row in zip(canonical_grid, truth)
        for before, after in zip(before_row, after_row)
    )
    return {
        "schema": "arc-zero-region-reference-probe-v1",
        "height": len(canonical_grid),
        "width": len(canonical_grid[0]),
        "input_sha256": _grid_sha256(canonical_grid),
        "reference_output_sha256": _grid_sha256(truth),
        "changed_cell_count": changed,
        "region_count": len(regions),
        "regions": region_rows,
        "input": canonical_grid,
        "reference_output": truth,
        "rivals": rival_rows,
    }


def _load_generator() -> tuple[Any, Path]:
    repo_root = Path(__file__).resolve().parents[3]
    runtime = repo_root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("probe_generator_60a8a9d74a75", generator_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {generator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, generator_path


def _source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _single_report(args: argparse.Namespace, generator: Any, generator_path: Path) -> dict[str, Any]:
    overrides = {"profile": args.profile} if args.profile else {}
    grid = generator.generate(
        args.seed,
        args.sample_index,
        difficulty=args.difficulty,
        **overrides,
    )
    report = analyze_grid(grid, rivals=generator.LESSON_COMPETITORS)
    report.update(
        {
            "task_id": generator.TASK_ID,
            "generator_sha256": _source_sha256(generator_path),
            "rule_hash": generator.RULE_HASH,
            "generation": {
                "seed": args.seed,
                "sample_index": args.sample_index,
                "difficulty": args.difficulty,
                "overrides": overrides,
                "observed": generator.observe_overrides(grid),
                "self_check": generator.self_check(grid),
            },
        }
    )
    return report


def _scan_report(args: argparse.Namespace, generator: Any, generator_path: Path) -> dict[str, Any]:
    profile_counts: dict[str, int] = {}
    crash_rows: list[dict[str, Any]] = []
    rival_disagreements = {name: 0 for name in generator.LESSON_COMPETITORS}
    unique_inputs: set[str] = set()
    changed_cells: list[int] = []
    max_region_sizes: list[int] = []
    for offset in range(args.scan):
        seed = args.seed + offset
        sample_index = args.sample_index + offset
        overrides = {"profile": args.profile} if args.profile else {}
        try:
            grid = generator.generate(seed, sample_index, difficulty=args.difficulty, **overrides)
            report = analyze_grid(grid, rivals=generator.LESSON_COMPETITORS)
        except Exception as exc:  # diagnostic CLI: retain all generation failures
            crash_rows.append(
                {
                    "seed": seed,
                    "sample_index": sample_index,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        profile = generator.observe_overrides(grid)["profile"]
        profile_counts[profile] = profile_counts.get(profile, 0) + 1
        unique_inputs.add(report["input_sha256"])
        changed_cells.append(report["changed_cell_count"])
        max_region_sizes.append(max(row["size"] for row in report["regions"]))
        for name, row in report["rivals"].items():
            rival_disagreements[name] += int(row["disagrees"])

    accepted = args.scan - len(crash_rows)
    return {
        "schema": "arc-zero-region-reference-scan-v1",
        "task_id": generator.TASK_ID,
        "generator_sha256": _source_sha256(generator_path),
        "rule_hash": generator.RULE_HASH,
        "request": {
            "seed_start": args.seed,
            "sample_index_start": args.sample_index,
            "draws": args.scan,
            "difficulty": args.difficulty,
            "profile_override": args.profile,
        },
        "accepted": accepted,
        "crash_count": len(crash_rows),
        "crashes": crash_rows,
        "unique_input_count": len(unique_inputs),
        "profile_counts": dict(sorted(profile_counts.items())),
        "rival_disagreement_counts": rival_disagreements,
        "changed_cells": {
            "min": min(changed_cells) if changed_cells else None,
            "max": max(changed_cells) if changed_cells else None,
        },
        "max_zero_region_size": {
            "min": min(max_region_sizes) if max_region_sizes else None,
            "max": max(max_region_sizes) if max_region_sizes else None,
        },
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=901)
    parser.add_argument("--sample-index", type=int, default=1)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="hard")
    parser.add_argument("--profile", default=None)
    parser.add_argument("--scan", type=int, default=0, metavar="N", help="scan N consecutive draws")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    if args.scan < 0:
        parser.error("--scan must be nonnegative")
    return args


def main() -> int:
    args = _parse_args()
    generator, generator_path = _load_generator()
    if args.profile is not None and args.profile not in generator.SCHEDULE_PROFILES:
        raise SystemExit(f"unknown profile {args.profile!r}; choose from {generator.SCHEDULE_PROFILES}")
    report = (
        _scan_report(args, generator, generator_path)
        if args.scan
        else _single_report(args, generator, generator_path)
    )
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
