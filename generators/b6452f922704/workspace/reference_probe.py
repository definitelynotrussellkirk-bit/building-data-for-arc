"""Independent geometry oracle and inspection helpers for b6452f922704.

This module deliberately does not import the production generator.  It is used by
focused reviewer tests and can be reused by future audits to inspect exact
frame/overlap geometry without consulting the Racket implementation.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Iterable


def load_generator(path: str | Path | None = None):
    if path is None:
        path = Path(__file__).resolve().parents[1] / "generator.py"
    source = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_b6452f922704", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    result: list[list[tuple[int, int]]] = []
    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                point = (row + dr, col + dc)
                if point in unseen:
                    unseen.remove(point)
                    stack.append(point)
                    cells.append(point)
        result.append(cells)
    return result


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    points = list(cells)
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return min(rows), max(rows), min(cols), max(cols)


def _perimeter(r0: int, r1: int, c0: int, c1: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if row in (r0, r1) or col in (c0, c1)
    }


def overlap_parts(grid: list[list[int]]) -> list[dict[str, Any]]:
    """Recover ordered frame geometry and authoritative output-part dimensions."""
    found: list[dict[str, Any]] = []
    for cells in _components(grid, 9):
        r0, r1, c0, c1 = _bbox(cells)
        if set(cells) != _perimeter(r0, r1, c0, c1):
            continue
        if r0 == 0:
            raise ValueError("frame has no row available for a key")
        keys = [
            grid[r0 - 1][col]
            for col in range(c0, c1 + 1)
            if grid[r0 - 1][col] not in (0, 9)
        ]
        if len(keys) != 1:
            raise ValueError(f"frame {(r0, c0)} has {len(keys)} keys")
        interior = [
            (row, col)
            for row in range(r0 + 1, r1)
            for col in range(c0 + 1, c1)
        ]
        blue = [point for point in interior if grid[point[0]][point[1]] == 1]
        red = [point for point in interior if grid[point[0]][point[1]] == 2]
        if not blue or not red:
            raise ValueError(f"frame {(r0, c0)} lacks a blue or red shape")
        br0, br1, bc0, bc1 = _bbox(blue)
        rr0, rr1, rc0, rc1 = _bbox(red)
        part_h = min(br1, rr1) - max(br0, rr0) + 1
        part_w = min(bc1, rc1) - max(bc0, rc0) + 1
        if part_h <= 0 or part_w <= 0:
            raise ValueError(f"frame {(r0, c0)} has disjoint bounding boxes")
        found.append(
            {
                "origin": (r0, c0),
                "frame_h": r1 - r0 + 1,
                "frame_w": c1 - c0 + 1,
                "key": keys[0],
                "part_h": part_h,
                "part_w": part_w,
            }
        )
    return sorted(found, key=lambda part: part["origin"])


def gallery_output(grid: list[list[int]], *, vertical: str = "center") -> list[list[int]]:
    """Independent rule mirror; ``vertical='top'`` is the canonical-fit rival."""
    parts = overlap_parts(grid)
    if not parts:
        raise ValueError("no frames")
    height = max(part["part_h"] for part in parts)
    width = sum(part["part_w"] for part in parts) + len(parts) - 1
    output = [[0 for _ in range(width)] for _ in range(height)]
    left = 0
    for part in parts:
        if vertical == "center":
            top = (height - part["part_h"]) // 2
        elif vertical == "top":
            top = 0
        else:
            raise ValueError(f"unknown vertical policy {vertical!r}")
        for row in range(top, top + part["part_h"]):
            for col in range(left, left + part["part_w"]):
                output[row][col] = part["key"]
        left += part["part_w"] + 1
    return output


def observed_axes(grid: list[list[int]]) -> dict[str, int]:
    parts = overlap_parts(grid)
    frame_heights = {part["frame_h"] for part in parts}
    frame_widths = {part["frame_w"] for part in parts}
    if len(parts) != 3 or len(frame_heights) != 1 or len(frame_widths) != 1:
        raise ValueError("expected exactly three equal-sized frames")
    return {
        "frame_h": frame_heights.pop(),
        "frame_w": frame_widths.pop(),
        "key_variety": len({part["key"] for part in parts}),
    }


def is_vertical_centering_witness(grid: list[list[int]]) -> bool:
    parts = overlap_parts(grid)
    tallest = max(part["part_h"] for part in parts)
    return any((tallest - part["part_h"]) // 2 > 0 for part in parts)
