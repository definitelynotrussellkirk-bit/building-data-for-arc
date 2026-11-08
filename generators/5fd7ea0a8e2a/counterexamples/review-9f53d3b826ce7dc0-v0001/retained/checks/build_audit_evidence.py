#!/usr/bin/env python3
"""Reproduce the two findings in AUDIT.md without external dependencies."""
from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def norm_grid(value: Any) -> list[list[int]]:
    if all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def canonical(task_id: str) -> dict[str, Any]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == task_id:
                return row
    raise RuntimeError(task_id)


def pairs(row: dict[str, Any]) -> list[dict[str, list[list[int]]]]:
    out = []
    for split in ("train", "test"):
        values = row.get(split, [])
        values = [values] if isinstance(values, dict) else values
        for pair in values:
            out.append({"input": norm_grid(pair["input"]), "output": norm_grid(pair["output"])})
    return out


def components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        result.append(sorted(cells))
    return result


def bbox(cells: list[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def bbox_area(cells: list[tuple[int, int]]) -> int:
    r1, c1, r2, c2 = bbox(cells)
    return (r2 - r1 + 1) * (c2 - c1 + 1)


def paint_components(
    grid: list[list[int]],
    ordered: list[tuple[list[tuple[int, int]], int]],
) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for cells, color in ordered:
        for r, c in cells:
            out[r][c] = color
    return out


def bbox_rank_rule(grid: list[list[int]]) -> list[list[int]]:
    comps = components([[1 if v else 0 for v in row] for row in grid], 1)
    comps.sort(key=lambda cells: bbox_area(cells), reverse=True)
    return paint_components(grid, [(cells, rank) for rank, cells in enumerate(comps, 2)])


def contains(outer: tuple[int, int, int, int], inner: tuple[int, int, int, int]) -> bool:
    return (
        outer != inner
        and outer[0] < inner[0]
        and outer[1] < inner[1]
        and outer[2] > inner[2]
        and outer[3] > inner[3]
    )


def containment_depth_rule(grid: list[list[int]]) -> list[list[int]]:
    comps = components([[1 if v else 0 for v in row] for row in grid], 1)
    boxes = [bbox(cells) for cells in comps]
    ranked = []
    for index, cells in enumerate(comps):
        depth = sum(contains(other, boxes[index]) for other in boxes)
        ranked.append((cells, 2 + depth))
    return paint_components(grid, ranked)


def changed(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    return [[r, c] for r, row in enumerate(left) for c, value in enumerate(row) if right[r][c] != value]


def recolor_all_matches(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    target = sum(value == 1 for value in grid[0])
    for cells in components(grid, 2):
        if len(cells) == target:
            for r, c in cells:
                out[r][c] = 3
    return out


def recolor_first_match(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    target = sum(value == 1 for value in grid[0])
    for cells in sorted(components(grid, 2), key=min):
        if len(cells) == target:
            for r, c in cells:
                out[r][c] = 3
            break
    return out


def main() -> None:
    nested_id = "2d5acf84dd20"
    nested_gen = load(nested_id)
    emitted = nested_gen.generate(0, 0, difficulty="easy")
    authority = bbox_rank_rule(emitted)
    depth_rival = containment_depth_rule(emitted)
    nested_canonical = pairs(canonical(nested_id))

    marker_id = "5fd7ea0a8e2a"
    marker_gen = load(marker_id)
    duplicate_match = [
        [0, 1, 0, 1, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 2, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    marker_canonical = pairs(canonical(marker_id))
    census: dict[str, dict[str, int]] = {}
    for band in ("easy", "medium", "hard"):
        counts: Counter[int] = Counter()
        for seed in range(200):
            grid = marker_gen.generate(seed, seed * 7 + 3, difficulty=band)
            target = sum(value == 1 for value in grid[0])
            counts[sum(len(cells) == target for cells in components(grid, 2))] += 1
        census[band] = {str(key): value for key, value in sorted(counts.items())}

    report = {
        nested_id: {
            "finding": "bbox-area implementation and generator drift from nested-depth task semantics",
            "canonical_depth_rival_fits": all(
                containment_depth_rule(pair["input"]) == pair["output"]
                for pair in nested_canonical
            ),
            "generated_seed": 0,
            "generated_sample_index": 0,
            "generated_difficulty": "easy",
            "generated_input": emitted,
            "component_bbox_areas": sorted(
                (bbox_area(cells) for cells in components(emitted, 1)), reverse=True
            ),
            "bbox_rank_output": authority,
            "containment_depth_output": depth_rival,
            "differing_output_cells": changed(authority, depth_rival),
        },
        marker_id: {
            "finding": "single-match-only distribution leaves recolor-first-match rival alive",
            "canonical_first_match_rival_fits": all(
                recolor_first_match(pair["input"]) == pair["output"]
                for pair in marker_canonical
            ),
            "counterexample_input": duplicate_match,
            "intended_output": recolor_all_matches(duplicate_match),
            "first_match_rival_output": recolor_first_match(duplicate_match),
            "differing_output_cells": changed(
                recolor_all_matches(duplicate_match), recolor_first_match(duplicate_match)
            ),
            "generated_match_count_census_200_per_band": census,
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
