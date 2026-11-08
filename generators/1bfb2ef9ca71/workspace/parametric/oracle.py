"""Independent Python semantics for the 1bfb2ef9ca71 parametric family."""
from __future__ import annotations


def rectangles(grid: list[list[int]]) -> list[dict[str, object]]:
    colors = sorted({value for row in grid for value in row if value != 0})
    result = []
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 2:
            raise ValueError(f"color {color} must appear exactly twice")
        (r0, c0), (r1, c1) = cells
        if r0 == r1 or c0 == c1:
            raise ValueError(f"color {color} endpoints must be diagonal")
        top, bottom = sorted((r0, r1))
        left, right = sorted((c0, c1))
        height, width = bottom - top + 1, right - left + 1
        border = {
            *[(top, c) for c in range(left, right + 1)],
            *[(bottom, c) for c in range(left, right + 1)],
            *[(r, left) for r in range(top, bottom + 1)],
            *[(r, right) for r in range(top, bottom + 1)],
        }
        interior = [
            (r, c)
            for r in range(top + 1, bottom)
            for c in range(left + 1, right)
        ]
        result.append({
            "color": color,
            "bbox": (top, left, bottom, right),
            "height": height,
            "width": width,
            "border": sorted(border),
            "interior": interior,
            "interior_area": len(interior),
            "perimeter": len(border),
        })
    return result


def borders_only(grid: list[list[int]]) -> list[list[int]]:
    out = [[0 for _ in row] for row in grid]
    for rect in rectangles(grid):
        for r, c in rect["border"]:
            out[r][c] = rect["color"]
    return out


def _winner(rects: list[dict[str, object]]) -> dict[str, object]:
    if not rects:
        raise ValueError("at least one rectangle is required")
    return sorted(
        rects,
        key=lambda rect: (
            -int(rect["interior_area"]),
            rect["bbox"][0],
            rect["bbox"][1],
        ),
    )[0]


def fill_largest_interior(grid: list[list[int]]) -> list[list[int]]:
    rects = rectangles(grid)
    winner = _winner(rects)
    out = borders_only(grid)
    for r, c in winner["interior"]:
        out[r][c] = winner["color"]
    return out


def solve(grid: list[list[int]], finish: str) -> list[list[int]]:
    if finish == "borders_only":
        return borders_only(grid)
    if finish == "fill_largest_interior":
        return fill_largest_interior(grid)
    raise ValueError(f"unknown finish: {finish}")


def describe(grid: list[list[int]], finish: str) -> dict[str, object]:
    rects = rectangles(grid)
    winner = _winner(rects)
    longest = sorted(
        rects,
        key=lambda rect: (-int(rect["perimeter"]), rect["bbox"][0], rect["bbox"][1]),
    )[0]
    largest_bbox = sorted(
        rects,
        key=lambda rect: (
            -int(rect["height"]) * int(rect["width"]),
            rect["bbox"][0],
            rect["bbox"][1],
        ),
    )[0]
    areas = [int(rect["interior_area"]) for rect in rects]
    return {
        "finish": finish,
        "shape": [len(grid), len(grid[0])],
        "rectangles": len(rects),
        "total_border_cells": sum(int(rect["perimeter"]) for rect in rects),
        "winner_color": winner["color"],
        "winner_bbox": list(winner["bbox"]),
        "winner_interior_area": winner["interior_area"],
        "longest_perimeter_color": longest["color"],
        "largest_bbox_color": largest_bbox["color"],
        "unique_largest_interior": areas.count(max(areas)) == 1,
        "interior_areas": sorted(areas),
    }
