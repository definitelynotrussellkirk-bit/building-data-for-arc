#!/usr/bin/env python3
"""Mine executable component-filter shortcuts against canonical and generated data.

The analysis is intentionally independent of generator-private component, rule,
witness, and rival helpers.  It imports only the public ``generate`` entry point
and reconstructs 4-connected components and expected outputs locally.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

WORKSPACE = Path(__file__).resolve().parent
REPO_ROOT = WORKSPACE.parents[2]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
DEFAULT_GENERATOR = WORKSPACE.parent / "generator.py"
DEFAULT_CANONICAL = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"

Grid = list[list[int]]
Cell = tuple[int, int]
Component = dict[str, Any]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _bbox(cells: set[Cell]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _has_full_2x2(cells: set[Cell]) -> bool:
    return any(
        {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
        <= cells
        for row, col in cells
    )


def _has_adjacency_cycle(cells: set[Cell]) -> bool:
    edge_count = sum(
        (row + dr, col + dc) in cells
        for row, col in cells
        for dr, dc in ((1, 0), (0, 1))
    )
    return edge_count >= len(cells)


def _has_enclosed_hole(cells: set[Cell]) -> bool:
    r1, c1, r2, c2 = _bbox(cells)
    background = {
        (row, col)
        for row in range(r1, r2 + 1)
        for col in range(c1, c2 + 1)
        if (row, col) not in cells
    }
    frontier = [
        cell
        for cell in background
        if cell[0] in (r1, r2) or cell[1] in (c1, c2)
    ]
    reachable = set(frontier)
    while frontier:
        row, col = frontier.pop()
        for dr, dc in _CARDINAL:
            neighbor = (row + dr, col + dc)
            if neighbor in background and neighbor not in reachable:
                reachable.add(neighbor)
                frontier.append(neighbor)
    return bool(background - reachable)


def component_properties(grid: Grid) -> list[Component]:
    """Return independently reconstructed same-color 4-components."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[Component] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: set[Cell] = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _CARDINAL:
                    neighbor = (row + dr, col + dc)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            r1, c1, r2, c2 = _bbox(cells)
            area = (r2 - r1 + 1) * (c2 - c1 + 1)
            missing = {
                (row, col)
                for row in range(r1, r2 + 1)
                for col in range(c1, c2 + 1)
                if (row, col) not in cells
            }
            max_fill_distance = max(
                (
                    min(
                        abs(row - other_row) + abs(col - other_col)
                        for other_row, other_col in cells
                    )
                    for row, col in missing
                ),
                default=0,
            )
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (r1, c1, r2, c2),
                    "bbox_height": r2 - r1 + 1,
                    "bbox_width": c2 - c1 + 1,
                    "bbox_area": area,
                    "size": len(cells),
                    "fill_gain": area - len(cells),
                    "density_numerator": len(cells),
                    "max_fill_manhattan_distance": max_fill_distance,
                    "has_full_2x2": _has_full_2x2(cells),
                    "has_adjacency_cycle": _has_adjacency_cycle(cells),
                    "has_enclosed_hole": _has_enclosed_hole(cells),
                }
            )
    return components


def _paint_selected(grid: Grid, selected: list[Component]) -> Grid:
    output = [row[:] for row in grid]
    for component in selected:
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                output[row][col] = component["color"]
    return output


def intended_output(grid: Grid) -> Grid:
    blank = [[0 for _ in row] for row in grid]
    return _paint_selected(blank, component_properties(grid))


def _filter_rival(predicate: Callable[[Component, Grid], bool]) -> Callable[[Grid], Grid]:
    def rival(grid: Grid) -> Grid:
        selected = [
            component
            for component in component_properties(grid)
            if predicate(component, grid)
        ]
        return _paint_selected(grid, selected)

    return rival


def _two_largest_components(grid: Grid) -> Grid:
    components = component_properties(grid)
    selected = sorted(
        components,
        key=lambda component: (component["fill_gain"], component["size"]),
        reverse=True,
    )[:2]
    return _paint_selected(grid, selected)


def _largest_component_per_color(grid: Grid) -> Grid:
    components = component_properties(grid)
    selected = []
    for color in sorted({component["color"] for component in components}):
        selected.append(
            max(
                (
                    component
                    for component in components
                    if component["color"] == color
                ),
                key=lambda component: (
                    component["fill_gain"],
                    component["size"],
                ),
            )
        )
    return _paint_selected(grid, selected)


def _near_corner(component: Component, grid: Grid, margin: int = 2) -> bool:
    height, width = len(grid), len(grid[0])
    r1, c1, r2, c2 = component["bbox"]
    return (
        min(r1, height - 1 - r2) <= margin
        and min(c1, width - 1 - c2) <= margin
    )


def _near_edge(component: Component, grid: Grid, margin: int = 2) -> bool:
    height, width = len(grid), len(grid[0])
    r1, c1, r2, c2 = component["bbox"]
    return min(r1, c1, height - 1 - r2, width - 1 - c2) <= margin


def _fill_manhattan_distance_at_most_one(grid: Grid) -> Grid:
    output = [row[:] for row in grid]
    for component in component_properties(grid):
        r1, c1, r2, c2 = component["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                distance = min(
                    abs(row - other_row) + abs(col - other_col)
                    for other_row, other_col in component["cells"]
                )
                if distance <= 1:
                    output[row][col] = component["color"]
    return output


def _diagonally_touch(first: Component, second: Component) -> bool:
    return any(
        (row + dr, col + dc) in second["cells"]
        for row, col in first["cells"]
        for dr, dc in _DIAGONAL
    )


def _min_manhattan_distance(first: Component, second: Component) -> int:
    return min(
        abs(row - other_row) + abs(col - other_col)
        for row, col in first["cells"]
        for other_row, other_col in second["cells"]
    )


def _largest_per_color_unless_equal_diagonal_or_far(grid: Grid) -> Grid:
    components = component_properties(grid)
    selected = []
    for color in sorted({component["color"] for component in components}):
        group = [component for component in components if component["color"] == color]
        easy_split = len({component["size"] for component in group}) == 1
        for index, first in enumerate(group):
            for second in group[index + 1 :]:
                easy_split = easy_split or _diagonally_touch(first, second)
                easy_split = easy_split or _min_manhattan_distance(first, second) >= 4
        if len(group) == 1 or easy_split:
            selected.extend(group)
        else:
            selected.append(
                max(
                    group,
                    key=lambda component: (
                        component["fill_gain"],
                        component["size"],
                    ),
                )
            )
    return _paint_selected(grid, selected)


RIVALS: dict[str, Callable[[Grid], Grid]] = {
    "corner_components_only": _filter_rival(_near_corner),
    "edge_components_only": _filter_rival(_near_edge),
    "bbox_extent_at_most_three": _filter_rival(
        lambda component, _grid: max(
            component["bbox_height"], component["bbox_width"]
        )
        <= 3
    ),
    "two_largest_components": _two_largest_components,
    "largest_component_per_color": _largest_component_per_color,
    "thin_components_only": _filter_rival(
        lambda component, _grid: not component["has_full_2x2"]
    ),
    "acyclic_components_only": _filter_rival(
        lambda component, _grid: not component["has_adjacency_cycle"]
    ),
    "hole_free_components_only": _filter_rival(
        lambda component, _grid: not component["has_enclosed_hole"]
    ),
    "bbox_density_at_most_five_sixths": _filter_rival(
        lambda component, _grid: (
            component["density_numerator"] * 6 <= component["bbox_area"] * 5
        )
    ),
    "component_size_at_most_eight": _filter_rival(
        lambda component, _grid: component["size"] <= 8
    ),
    "fill_manhattan_distance_at_most_one": _fill_manhattan_distance_at_most_one,
    "fill_gain_at_most_four": _filter_rival(
        lambda component, _grid: component["fill_gain"] <= 4
    ),
    "bbox_density_at_least_five_ninths": _filter_rival(
        lambda component, _grid: (
            component["density_numerator"] * 9 >= component["bbox_area"] * 5
        )
    ),
    "aspect_ratio_at_most_three_halves": _filter_rival(
        lambda component, _grid: (
            max(component["bbox_height"], component["bbox_width"]) * 2
            <= min(component["bbox_height"], component["bbox_width"]) * 3
        )
    ),
    "bbox_area_at_most_sixteen": _filter_rival(
        lambda component, _grid: component["bbox_area"] <= 16
    ),
    "component_size_at_most_fifteen": _filter_rival(
        lambda component, _grid: component["size"] <= 15
    ),
    "extent_at_most_three_or_square": _filter_rival(
        lambda component, _grid: (
            max(component["bbox_height"], component["bbox_width"]) <= 3
            or component["bbox_height"] == component["bbox_width"]
        )
    ),
    "largest_per_color_unless_equal_diagonal_or_far": (
        _largest_per_color_unless_equal_diagonal_or_far
    ),
}


def _load_generator(path: Path):
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if str(RUNTIME_ROOT) not in sys.path:
        sys.path.insert(0, str(RUNTIME_ROOT))
    module_name = f"shortcut_miner_generator_{source_hash[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, source_hash


def _canonical_pairs(path: Path, task_id: str) -> list[dict[str, Any]]:
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == task_id:
            return list(row.get("train", [])) + list(row.get("test", []))
    raise ValueError(f"task {task_id!r} not found in {path}")


def _json_key(grid: Grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def run_miner(
    generator_path: Path,
    *,
    canonical_path: Path,
    seed_start: int,
    samples_per_profile: int,
    difficulties: tuple[str, ...],
    grid_h: int,
    grid_w: int,
) -> dict[str, Any]:
    generator_path = generator_path.resolve()
    generator, source_hash = _load_generator(generator_path)
    task_id = str(getattr(generator, "TASK_ID", "unknown"))
    profiles = tuple(generator.SCENE_PROFILES)
    pairs = _canonical_pairs(canonical_path, task_id)
    canonical_stats = {
        name: sum(rival(pair["input"]) == pair["output"] for pair in pairs)
        for name, rival in RIVALS.items()
    }

    attempts = len(difficulties) * len(profiles) * samples_per_profile
    successful = 0
    unique_inputs: set[str] = set()
    generation_failures: list[dict[str, Any]] = []
    property_grids: Counter[str] = Counter()
    disagreements: dict[str, Counter[str]] = {
        name: Counter() for name in RIVALS
    }
    first_counterexample: dict[str, dict[str, Any]] = {}

    for difficulty in difficulties:
        for profile_index, profile in enumerate(profiles):
            for seed in range(seed_start, seed_start + samples_per_profile):
                sample_index = seed * len(profiles) + profile_index
                try:
                    grid = generator.generate(
                        seed,
                        sample_index,
                        difficulty=difficulty,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        scene_profile=profile,
                    )
                except Exception as exc:
                    generation_failures.append(
                        {
                            "difficulty": difficulty,
                            "scene_profile": profile,
                            "seed": seed,
                            "sample_index": sample_index,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    continue
                successful += 1
                unique_inputs.add(_json_key(grid))
                components = component_properties(grid)
                changed = [component for component in components if component["fill_gain"]]
                properties = {
                    "full_2x2": any(component["has_full_2x2"] for component in changed),
                    "adjacency_cycle": any(
                        component["has_adjacency_cycle"] for component in changed
                    ),
                    "enclosed_hole": any(
                        component["has_enclosed_hole"] for component in changed
                    ),
                    "density_over_five_sixths": any(
                        component["density_numerator"] * 6
                        > component["bbox_area"] * 5
                        for component in changed
                    ),
                    "size_over_eight": any(
                        component["size"] > 8 for component in changed
                    ),
                    "fill_gain_over_four": any(
                        component["fill_gain"] > 4 for component in changed
                    ),
                    "bbox_area_over_sixteen": any(
                        component["bbox_area"] > 16 for component in changed
                    ),
                    "density_below_five_ninths": any(
                        component["density_numerator"] * 9
                        < component["bbox_area"] * 5
                        for component in changed
                    ),
                    "max_fill_distance_over_three": any(
                        component["max_fill_manhattan_distance"] > 3
                        for component in changed
                    ),
                    "aspect_over_three_halves": any(
                        max(component["bbox_height"], component["bbox_width"]) * 2
                        > min(component["bbox_height"], component["bbox_width"]) * 3
                        for component in changed
                    ),
                    "size_over_fifteen": any(
                        component["size"] > 15 for component in changed
                    ),
                }
                for name, present in properties.items():
                    if present:
                        property_grids[name] += 1
                expected = intended_output(grid)
                for name, rival in RIVALS.items():
                    rival_output = rival(grid)
                    if rival_output == expected:
                        continue
                    disagreements[name][profile] += 1
                    if name not in first_counterexample:
                        first_counterexample[name] = {
                            "difficulty": difficulty,
                            "scene_profile": profile,
                            "seed": seed,
                            "sample_index": sample_index,
                            "input": grid,
                            "intended_output": expected,
                            "rival_output": rival_output,
                        }

    fits_all_canonical = sorted(
        name for name, count in canonical_stats.items() if count == len(pairs)
    )
    survives_generated = sorted(
        name
        for name in fits_all_canonical
        if sum(disagreements[name].values()) == 0
    )
    return {
        "schema": "arc-generator-shortcut-miner-v2",
        "task_id": task_id,
        "generator_version": str(getattr(generator, "VERSION", "unknown")),
        "source": {"path": str(generator_path), "sha256": source_hash},
        "parameters": {
            "seed_start_inclusive": seed_start,
            "seed_end_exclusive": seed_start + samples_per_profile,
            "samples_per_profile_per_difficulty": samples_per_profile,
            "difficulties": list(difficulties),
            "scene_profiles": list(profiles),
            "grid_h": grid_h,
            "grid_w": grid_w,
            "sample_index_formula": "seed * len(scene_profiles) + profile_index",
        },
        "denominator": {
            "canonical_pairs": len(pairs),
            "generated_attempts": attempts,
            "successful_grids": successful,
            "unique_inputs": len(unique_inputs),
        },
        "canonical_matches": {
            name: {"pairs": canonical_stats[name], "of": len(pairs)}
            for name in sorted(RIVALS)
        },
        "canonical_fitting_shortcuts": fits_all_canonical,
        "generated_property_grid_counts": dict(sorted(property_grids.items())),
        "rival_disagreements": {
            name: {
                "grids": sum(disagreements[name].values()),
                "by_profile": dict(sorted(disagreements[name].items())),
            }
            for name in sorted(RIVALS)
        },
        "canonical_shortcuts_surviving_generated_sample": survives_generated,
        "first_counterexample": first_counterexample,
        "generation_failures": generation_failures,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--canonical", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--samples-per-profile", type=int, default=100)
    parser.add_argument(
        "--difficulties", nargs="+", default=("easy", "medium", "hard")
    )
    parser.add_argument("--grid-h", type=int, default=8)
    parser.add_argument("--grid-w", type=int, default=9)
    args = parser.parse_args()
    if args.samples_per_profile <= 0:
        parser.error("--samples-per-profile must be positive")
    return args


def main() -> int:
    args = _parse_args()
    report = run_miner(
        args.generator,
        canonical_path=args.canonical,
        seed_start=args.seed_start,
        samples_per_profile=args.samples_per_profile,
        difficulties=tuple(args.difficulties),
        grid_h=args.grid_h,
        grid_w=args.grid_w,
    )
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        sys.stdout.write(encoded)
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
        print(args.out)
    return 1 if report["generation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
