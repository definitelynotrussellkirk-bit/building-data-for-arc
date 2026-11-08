#!/usr/bin/env python3
"""Independent morphology/support probe for generator cc8c719680e6.

The probe calls only ``generate`` on the producer module.  Components, official
outputs, canonical joint profiles, and shortcut support are reconstructed from
returned grids plus the portable canonical ledger.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

TASK_ID = "cc8c719680e6"
EXAMPLES_NEEDED = 4
LEGACY_SPANS = {(2, 2), (3, 2), (3, 3), (3, 4)}

Grid = list[list[int]]
Cell = tuple[int, int]
Component = dict[str, Any]


def _load_generator(path: Path):
    repo_root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(repo_root / "shared" / "runtime"), str(repo_root / "shared" / "tools")]
    from generator_module_loader import load_module_from_path

    return load_module_from_path(f"probe_{TASK_ID}_{hash(path)}", path)


def _canonical_inputs() -> list[Grid]:
    from reviewer_support import canonical_pairs, find_root

    root = find_root(__file__)
    return [pair["input"] for pair in canonical_pairs(TASK_ID, root=root)]


def _grid_key(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _components(grid: Grid) -> list[Component]:
    """Return same-color nonzero 4-connected components in row-major order."""
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    components: list[Component] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells: set[Cell] = set()
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                cells.add((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [cell[0] for cell in cells]
            cols = [cell[1] for cell in cells]
            components.append(
                {
                    "color": color,
                    "cells": frozenset(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return components


def _shape_key(component: Component) -> tuple[Cell, ...]:
    r0, c0, _, _ = component["bbox"]
    return tuple(sorted((r - r0, c - c0) for r, c in component["cells"]))


def _span(component: Component) -> tuple[int, int]:
    r0, c0, r1, c1 = component["bbox"]
    return r1 - r0 + 1, c1 - c0 + 1


def _touches_border(component: Component, h: int, w: int) -> bool:
    r0, c0, r1, c1 = component["bbox"]
    return r0 == 0 or c0 == 0 or r1 == h - 1 or c1 == w - 1


def _joint_profile(grid: Grid) -> tuple[Any, ...]:
    h, w = len(grid), len(grid[0])
    components = _components(grid)
    return (
        h,
        w,
        any(_touches_border(component, h, w) for component in components),
        tuple(sorted(_shape_key(component) for component in components)),
    )


def _canonical_joint_profiles() -> set[tuple[Any, ...]]:
    return {_joint_profile(grid) for grid in _canonical_inputs()}


def _rule_output(grid: Grid) -> Grid:
    """Independent Python reconstruction of the selected bbox-outline rule."""
    h, w = len(grid), len(grid[0])
    output = [[0 for _ in range(w)] for _ in range(h)]
    for component in _components(grid):
        r0, c0, r1, c1 = component["bbox"]
        color = component["color"]
        for c in range(c0, c1 + 1):
            output[r0][c] = color
            output[r1][c] = color
        for r in range(r0, r1 + 1):
            output[r][c0] = color
            output[r][c1] = color
    return output


def measure(generator_path: Path, seeds: int) -> dict[str, Any]:
    gen = _load_generator(generator_path)
    source_hash = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    canonical_profiles_expected = _canonical_joint_profiles()
    report: dict[str, Any] = {
        "schema": "cc8c719680e6-morphology-probe-v2",
        "task_id": TASK_ID,
        "generator": str(generator_path),
        "generator_sha256": source_hash,
        "seeds_per_band": seeds,
        "producer_api_used": ["generate"],
        "canonical_joint_profile_count": len(canonical_profiles_expected),
        "bands": {},
    }

    for difficulty in ("easy", "medium", "hard"):
        spans: Counter[tuple[int, int]] = Counter()
        areas: Counter[int] = Counter()
        normalized_shapes: set[tuple[Cell, ...]] = set()
        inputs: set[tuple[tuple[int, ...], ...]] = set()
        outputs: set[tuple[tuple[int, ...], ...]] = set()
        canonical_profiles: set[tuple[Any, ...]] = set()
        windows_without_novel: list[dict[str, int]] = []

        for seed in range(seeds):
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                inputs.add(_grid_key(grid))
                outputs.add(_grid_key(_rule_output(grid)))
                profile = _joint_profile(grid)
                if profile in canonical_profiles_expected:
                    canonical_profiles.add(profile)
                for component in _components(grid):
                    spans[_span(component)] += 1
                    areas[len(component["cells"])] += 1
                    normalized_shapes.add(_shape_key(component))

        for start in range(8):
            lesson = [
                gen.generate(100_000 + start, index, difficulty=difficulty)
                for index in range(start, start + EXAMPLES_NEEDED)
            ]
            if not any(
                _span(component) not in LEGACY_SPANS
                for grid in lesson
                for component in _components(grid)
            ):
                windows_without_novel.append({"seed": 100_000 + start, "start": start})

        report["bands"][difficulty] = {
            "generated_grids": seeds * 4,
            "unique_inputs": len(inputs),
            "unique_outputs": len(outputs),
            "unique_normalized_shapes": len(normalized_shapes),
            "bbox_spans": {f"{h}x{w}": count for (h, w), count in sorted(spans.items())},
            "novel_bbox_spans": [
                f"{h}x{w}" for h, w in sorted(set(spans) - LEGACY_SPANS)
            ],
            "component_areas": {str(area): count for area, count in sorted(areas.items())},
            "canonical_joint_profiles_seen": [repr(item) for item in sorted(canonical_profiles)],
            "lesson_windows_without_novel_span": windows_without_novel,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--seeds", "--seeds-per-band", dest="seeds", type=int, default=250)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")

    report = measure(args.generator.resolve(), args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
