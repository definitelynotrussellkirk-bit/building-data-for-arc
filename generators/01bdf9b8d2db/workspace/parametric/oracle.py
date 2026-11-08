"""Independent Python semantics for the 01bdf9b8d2db parametric family."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

FINISHES = ("fill_all", "mark_smallest_total")


def regions(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and grid[point[0]][point[1]] != 5
                        and point not in seen
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(sorted(cells))
    return result


def chamber_rows(grid):
    rows = []
    for cells in regions(grid):
        markers = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)]
        if len(markers) != 1:
            raise ValueError(
                f"every non-wall chamber needs exactly one seed; observed {len(markers)}"
            )
        rows.append({"cells": cells, "color": markers[0], "area": len(cells)})
    return rows


def fill_all(grid):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for row in chamber_rows(grid):
        for r, c in row["cells"]:
            out[r][c] = row["color"]
    return out


def color_totals(filled):
    counts = Counter(value for row in filled for value in row if value not in (0, 5))
    return dict(sorted(counts.items()))


def selected_smallest_total(grid):
    filled = fill_all(grid)
    totals = color_totals(filled)
    if not totals:
        raise ValueError("at least one chamber color is required")
    return min(totals, key=lambda color: (totals[color], color))


def solve(grid, finish):
    if finish not in FINISHES:
        raise ValueError(f"unknown finish: {finish}")
    filled = fill_all(grid)
    if finish == "fill_all":
        return filled
    selected = min(
        color_totals(filled),
        key=lambda color: (color_totals(filled)[color], color),
    )
    return [[9 if value == selected else value for value in row] for row in filled]


def intermediate(grid):
    filled = fill_all(grid)
    totals = color_totals(filled)
    selected = min(totals, key=lambda color: (totals[color], color))
    return {
        "chambers": [
            {"area": row["area"], "seed_color": row["color"]}
            for row in chamber_rows(grid)
        ],
        "filled_color_totals": totals,
        "selected_color": selected,
    }


def validate_input(grid):
    errors = []
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
    ):
        return ["grid must be a nonempty 1..30 list of rows"]
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be exact integer ARC colors 0..9"]
    if any(value != 5 for value in grid[0] + grid[-1]) or any(
        row[0] != 5 or row[-1] != 5 for row in grid
    ):
        errors.append("outer border must be color 5")
    try:
        rows = chamber_rows(grid)
    except ValueError as exc:
        errors.append(str(exc))
        rows = []
    colors = {row["color"] for row in rows}
    if any(color not in range(1, 9) or color == 5 for color in colors):
        errors.append("seed colors must be drawn from 1..8 excluding wall color 5")
    if len(colors) < 3:
        errors.append("at least three seed colors are required")
    if rows:
        totals = color_totals(fill_all(grid))
        if len(set(totals.values())) != len(totals):
            errors.append("filled color totals must be distinct")
    return errors


def copy_grid(grid):
    return deepcopy(grid)
