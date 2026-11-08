"""Independent oracle and diagnostics for generator 5a01897eb8be.

This test helper mirrors the pinned Racket rule without importing implementation
helpers from ``generator.py``.  It is intentionally useful as a future-review
probe: run it directly to summarize generated support and rival refutations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
from typing import Any, Iterable

TASK_ID = "5a01897eb8be"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or ROOT / f"generators/{TASK_ID}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_5a01897eb8be", source)
    if spec is None or spec.loader is None:
        raise ImportError(source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("expected integer ARC colors 0..9")
    return len(grid), width


def _colors(grid: list[list[int]]) -> list[int]:
    bg = grid[0][0]
    return sorted({value for row in grid for value in row if value != bg})


def _count_extent(
    grid: list[list[int]], color: int, row: int, col: int, dr: int, dc: int
) -> int:
    height, width = len(grid), len(grid[0])
    length = 0
    while 0 <= row < height and 0 <= col < width and grid[row][col] == color:
        length += 1
        row += dr
        col += dc
    return length


def color_info(grid: list[list[int]], color: int) -> dict[str, Any]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    ]
    if not cells:
        raise ValueError(f"missing color {color}")
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    max_dim = max(bbox[2] - bbox[0] + 1, bbox[3] - bbox[1] + 1)
    arm = 0
    for row, col in cells:
        for dr in (-1, 1):
            for dc in (-1, 1):
                arm = max(
                    arm,
                    min(
                        _count_extent(grid, color, row, col, 0, dc),
                        _count_extent(grid, color, row, col, dr, 0),
                    ),
                )
    return {"color": color, "max_dim": max_dim, "arm": arm, "bbox": bbox, "cells": cells}


def analyze(grid: list[list[int]]) -> dict[str, Any]:
    height, width = _validate_grid(grid)
    bg = grid[0][0]
    infos = [color_info(grid, color) for color in _colors(grid)]
    count = len(infos)
    has_center = any(info["max_dim"] == 1 for info in infos)
    ring_sizes = [
        (1 if has_center else 3) + 2 * index for index in range(count)
    ]
    available = list(ring_sizes)
    assigned: list[tuple[dict[str, Any], int]] = []

    exact = [info for info in infos if info["max_dim"] in ring_sizes]
    loose = [info for info in infos if info["max_dim"] not in ring_sizes]
    for info in loose + sorted(exact, key=lambda item: -item["max_dim"]):
        target = next((ring for ring in available if ring >= info["max_dim"]), None)
        if target is None:
            raise ValueError(
                f"color {info['color']} with max-dim {info['max_dim']} fits no remaining ring"
            )
        available.remove(target)
        assigned.append((info, target))

    return {
        "height": height,
        "width": width,
        "background": bg,
        "infos": infos,
        "shape_count": count,
        "has_center": has_center,
        "loose_shape": bool(loose),
        "ring_sizes": ring_sizes,
        "assignments": assigned,
    }


def _l_cells(arm: int, size: int) -> set[tuple[int, int]]:
    top_left = {(0, step) for step in range(arm)} | {(step, 0) for step in range(arm)}
    result: set[tuple[int, int]] = set()
    for row, col in top_left:
        result.update(
            {
                (row, col),
                (row, size - 1 - col),
                (size - 1 - row, col),
                (size - 1 - row, size - 1 - col),
            }
        )
    return result


def _render(analysis: dict[str, Any], assignments, *, solid: bool = False) -> list[list[int]]:
    size = max(analysis["ring_sizes"])
    middle = size // 2
    output = [[analysis["background"] for _ in range(size)] for _ in range(size)]
    for info, ring_size in sorted(assignments, key=lambda item: -item[1]):
        arm = ring_size if solid else min(info["arm"], ring_size)
        offset = middle - ring_size // 2
        for row, col in _l_cells(arm, ring_size):
            output[offset + row][offset + col] = info["color"]
    return output


def intended_output(grid: list[list[int]]) -> list[list[int]]:
    details = analyze(grid)
    return _render(details, details["assignments"])


def first_appearance_colors(grid: list[list[int]]) -> list[int]:
    bg = grid[0][0]
    seen: set[int] = set()
    order: list[int] = []
    for row in grid:
        for value in row:
            if value != bg and value not in seen:
                seen.add(value)
                order.append(value)
    return order


def rival_scan_order(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: row-major first appearance directly names outer-to-inner rings."""
    details = analyze(grid)
    by_color = {info["color"]: info for info in details["infos"]}
    assignments = list(
        zip(
            (by_color[color] for color in first_appearance_colors(grid)),
            reversed(details["ring_sizes"]),
        )
    )
    return _render(details, assignments)


def rival_solid_rings(grid: list[list[int]]) -> list[list[int]]:
    """Wrong rule: measure/assign shape sizes correctly but fill every ring border."""
    details = analyze(grid)
    return _render(details, details["assignments"], solid=True)


def observed(grid: list[list[int]]) -> dict[str, Any]:
    details = analyze(grid)
    return {
        "grid_h": details["height"],
        "grid_w": details["width"],
        "shape_count": details["shape_count"],
        "has_center": details["has_center"],
        "background": details["background"],
        "loose_shape": details["loose_shape"],
    }


def component_sizes(grid: list[list[int]]) -> list[int]:
    """Sizes of monochrome 4-connected foreground objects."""
    bg = grid[0][0]
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != bg
    }
    sizes: list[int] = []
    while unseen:
        seed = unseen.pop()
        color = grid[seed[0]][seed[1]]
        stack = [seed]
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                point = (row + dr, col + dc)
                if point in unseen and grid[point[0]][point[1]] == color:
                    unseen.remove(point)
                    stack.append(point)
        sizes.append(size)
    return sorted(sizes)


def component_count(grid: list[list[int]]) -> int:
    """Count monochrome 4-connected foreground objects."""
    return len(component_sizes(grid))


def scan_order_is_size_order(grid: list[list[int]]) -> bool:
    details = analyze(grid)
    expected = [
        info["color"]
        for info, _ in sorted(details["assignments"], key=lambda item: -item[1])
    ]
    return first_appearance_colors(grid) == expected


def report(generator, *, count: int = 96, difficulty: str | None = None) -> dict[str, Any]:
    profiles: Counter[tuple[int, int, int]] = Counter()
    backgrounds: Counter[int] = Counter()
    components: list[int] = []
    scan_refuted = solid_refuted = 0
    errors: list[dict[str, Any]] = []
    for index in range(count):
        grid = generator.generate(9100 + index, index, difficulty=difficulty)
        check = generator.self_check(grid)
        if check:
            errors.append({"index": index, "errors": check})
            continue
        details = observed(grid)
        profiles[(details["grid_h"], details["grid_w"], details["shape_count"] + 1)] += 1
        backgrounds[details["background"]] += 1
        components.append(component_count(grid))
        expected = intended_output(grid)
        scan_refuted += rival_scan_order(grid) != expected
        solid_refuted += rival_solid_rings(grid) != expected
    return {
        "difficulty": difficulty,
        "count": count,
        "profiles": {str(key): value for key, value in sorted(profiles.items())},
        "backgrounds": dict(sorted(backgrounds.items())),
        "component_median": statistics.median(components) if components else None,
        "component_range": [min(components), max(components)] if components else None,
        "scan_order_refuted": scan_refuted,
        "solid_rings_refuted": solid_refuted,
        "errors": errors,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator")
    parser.add_argument("--count", type=int, default=96)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"))
    args = parser.parse_args(list(argv) if argv is not None else None)
    generator = load_generator(args.generator)
    print(json.dumps(report(generator, count=args.count, difficulty=args.difficulty), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
