#!/usr/bin/env python3
"""Source-hashed distribution probe for generator 297c05190f7c.

The probe intentionally reimplements the task rule and two shortcut rivals. It
therefore measures the selected generator without trusting its private analysis,
rule mirror, witnesses, or rival implementations.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

Grid = list[list[int]]
Cell = tuple[int, int]
BBox = tuple[int, int, int, int]
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

SCRIPT_PATH = Path(__file__).resolve()
TASK_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[3]
DEFAULT_GENERATOR = TASK_DIR / "generator.py"
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"


def components4(grid: Grid) -> list[dict[str, Any]]:
    """Return independently computed nonzero same-color 4-components."""
    height, width = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[dict[str, Any]] = []
    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue
            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells: set[Cell] = set()
            while queue:
                row, col = queue.popleft()
                cells.add((row, col))
                for dr, dc in _CARDINAL:
                    next_row, next_col = row + dr, col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            bbox = (min(rows), min(cols), max(rows), max(cols))
            bbox_height = bbox[2] - bbox[0] + 1
            bbox_width = bbox[3] - bbox[1] + 1
            components.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": bbox,
                    "bbox_height": bbox_height,
                    "bbox_width": bbox_width,
                    "solid": len(cells) == bbox_height * bbox_width,
                }
            )
    return components


def _fill_component_boxes(grid: Grid, predicate) -> Grid:
    output = copy.deepcopy(grid)
    for component in components4(grid):
        if not predicate(component):
            continue
        row1, col1, row2, col2 = component["bbox"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = component["color"]
    return output


def intended_output(grid: Grid) -> Grid:
    """Independent intended rule: fill each 4-component's tight box."""
    output = [[0 for _ in row] for row in grid]
    for component in components4(grid):
        row1, col1, row2, col2 = component["bbox"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = component["color"]
    return output


def bbox_near_public_corner(
    bbox: BBox, height: int, width: int, margin: int = 2
) -> bool:
    row1, col1, row2, col2 = bbox
    return (
        min(row1, height - 1 - row2) <= margin
        and min(col1, width - 1 - col2) <= margin
    )


def corner_components_only(grid: Grid, margin: int = 2) -> Grid:
    """Shortcut: complete only components whose box is near two outer edges."""
    height, width = len(grid), len(grid[0])
    return _fill_component_boxes(
        grid,
        lambda component: bbox_near_public_corner(
            component["bbox"], height, width, margin
        ),
    )


def bbox_extent_at_most_three(grid: Grid) -> Grid:
    """Shortcut: complete only components with maximum box extent <= 3."""
    return _fill_component_boxes(
        grid,
        lambda component: max(
            component["bbox_height"], component["bbox_width"]
        )
        <= 3,
    )


def summarize_grid(grid: Grid) -> dict[str, int]:
    """Return geometry counts used by the distribution report and regressions."""
    height, width = len(grid), len(grid[0])
    components = components4(grid)
    nonrectangular = [component for component in components if not component["solid"]]
    return {
        "component_count": len(components),
        "nonrectangular_components": len(nonrectangular),
        "noncorner_nonrectangular_components": sum(
            not bbox_near_public_corner(component["bbox"], height, width)
            for component in nonrectangular
        ),
        "bbox_extent_over_three_components": sum(
            max(component["bbox_height"], component["bbox_width"]) > 3
            for component in nonrectangular
        ),
    }


def _load_generator(path: Path):
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    if str(RUNTIME_ROOT) not in sys.path:
        sys.path.insert(0, str(RUNTIME_ROOT))
    module_name = f"distribution_probe_generator_{source_hash[:16]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator source at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module, source_hash


def _json_key(grid: Grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def run_probe(
    generator_path: Path,
    *,
    seed_start: int,
    samples_per_profile: int,
    difficulties: tuple[str, ...],
    grid_h: int,
    grid_w: int,
) -> dict[str, Any]:
    generator_path = generator_path.resolve()
    generator, source_hash = _load_generator(generator_path)
    profiles = tuple(generator.SCENE_PROFILES)
    profile_counts: Counter[str] = Counter()
    component_count_histogram: Counter[str] = Counter()
    bbox_extent_histogram: Counter[str] = Counter()
    grid_counts = Counter()
    rival_disagreements = Counter()
    rival_disagreements_by_profile = {
        "corner_components_only": Counter(),
        "bbox_extent_at_most_three": Counter(),
    }
    first_counterexample: dict[str, dict[str, Any]] = {}
    generation_failures: list[dict[str, Any]] = []
    self_check_failures: list[dict[str, Any]] = []
    unique_inputs: set[str] = set()

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
                except Exception as exc:  # retained in the JSON rather than hidden
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

                profile_counts[profile] += 1
                grid_counts["successful_grids"] += 1
                unique_inputs.add(_json_key(grid))
                errors = list(generator.self_check(grid))
                if errors:
                    self_check_failures.append(
                        {
                            "difficulty": difficulty,
                            "scene_profile": profile,
                            "seed": seed,
                            "sample_index": sample_index,
                            "errors": errors,
                        }
                    )

                summary = summarize_grid(grid)
                component_count_histogram[str(summary["component_count"])] += 1
                grid_counts["total_components"] += summary["component_count"]
                grid_counts["nonrectangular_components"] += summary[
                    "nonrectangular_components"
                ]
                grid_counts["noncorner_nonrectangular_components"] += summary[
                    "noncorner_nonrectangular_components"
                ]
                grid_counts["bbox_extent_over_three_components"] += summary[
                    "bbox_extent_over_three_components"
                ]
                if summary["noncorner_nonrectangular_components"]:
                    grid_counts["grids_with_noncorner_nonrectangular_component"] += 1
                if summary["bbox_extent_over_three_components"]:
                    grid_counts["grids_with_bbox_extent_over_three_component"] += 1

                for component in components4(grid):
                    extent = max(component["bbox_height"], component["bbox_width"])
                    bbox_extent_histogram[str(extent)] += 1

                intended = intended_output(grid)
                rivals = {
                    "corner_components_only": corner_components_only(grid),
                    "bbox_extent_at_most_three": bbox_extent_at_most_three(grid),
                }
                for rival_name, rival_output in rivals.items():
                    if rival_output == intended:
                        continue
                    rival_disagreements[rival_name] += 1
                    rival_disagreements_by_profile[rival_name][profile] += 1
                    if rival_name not in first_counterexample:
                        first_counterexample[rival_name] = {
                            "difficulty": difficulty,
                            "scene_profile": profile,
                            "seed": seed,
                            "sample_index": sample_index,
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "input": grid,
                            "intended_output": intended,
                            "rival_output": rival_output,
                        }

    expected_grids = len(difficulties) * len(profiles) * samples_per_profile
    return {
        "schema": "arc-generator-distribution-probe-v1",
        "task_id": str(getattr(generator, "TASK_ID", "unknown")),
        "generator_version": str(getattr(generator, "VERSION", "unknown")),
        "source": {
            "path": str(generator_path),
            "sha256": source_hash,
        },
        "parameters": {
            "seed_start_inclusive": seed_start,
            "seed_end_exclusive": seed_start + samples_per_profile,
            "samples_per_profile_per_difficulty": samples_per_profile,
            "difficulties": list(difficulties),
            "scene_profiles": list(profiles),
            "grid_h": grid_h,
            "grid_w": grid_w,
            "sample_index_formula": "seed * len(scene_profiles) + profile_index",
            "public_corner_margin": 2,
            "expected_grids": expected_grids,
        },
        "denominator": {
            "generated_grid_attempts": expected_grids,
            "successful_grids": grid_counts["successful_grids"],
            "unique_inputs": len(unique_inputs),
            "total_components": grid_counts["total_components"],
        },
        "profile_counts": dict(sorted(profile_counts.items())),
        "component_count_histogram": dict(sorted(component_count_histogram.items())),
        "bbox_max_extent_component_histogram": dict(
            sorted(bbox_extent_histogram.items(), key=lambda item: int(item[0]))
        ),
        "geometry_counts": {
            "nonrectangular_components": grid_counts["nonrectangular_components"],
            "noncorner_nonrectangular_components": grid_counts[
                "noncorner_nonrectangular_components"
            ],
            "bbox_extent_over_three_components": grid_counts[
                "bbox_extent_over_three_components"
            ],
            "grids_with_noncorner_nonrectangular_component": grid_counts[
                "grids_with_noncorner_nonrectangular_component"
            ],
            "grids_with_bbox_extent_over_three_component": grid_counts[
                "grids_with_bbox_extent_over_three_component"
            ],
        },
        "rival_disagreements": {
            name: {
                "grids": rival_disagreements[name],
                "by_profile": dict(
                    sorted(rival_disagreements_by_profile[name].items())
                ),
            }
            for name in (
                "corner_components_only",
                "bbox_extent_at_most_three",
            )
        },
        "first_counterexample": first_counterexample,
        "generation_failures": generation_failures,
        "self_check_failures": self_check_failures,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path, default=DEFAULT_GENERATOR)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--seed-start", type=int, default=0)
    parser.add_argument("--samples-per-profile", type=int, default=100)
    parser.add_argument(
        "--difficulties",
        nargs="+",
        default=("easy", "medium", "hard"),
    )
    parser.add_argument("--grid-h", type=int, default=8)
    parser.add_argument("--grid-w", type=int, default=9)
    args = parser.parse_args()
    if args.samples_per_profile <= 0:
        parser.error("--samples-per-profile must be positive")
    return args


def main() -> int:
    args = _parse_args()
    report = run_probe(
        args.generator,
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
    return 1 if report["generation_failures"] or report["self_check_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
