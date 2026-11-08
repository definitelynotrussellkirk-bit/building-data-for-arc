"""Independent structural oracle for e03758508612 reviewer tests.

This module never supplies production labels.  It parses cyan-wall regions and
implements the written legend-priority rule independently from generator.py.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

TASK_ID = "e03758508612"
HOME = Path(__file__).resolve().parents[1]


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def chambers(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Return 4-connected non-cyan regions below the legend, row-major."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for row in range(1, height):
        for column in range(width):
            if grid[row][column] == 8 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            cells: list[tuple[int, int]] = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbour = (r + dr, c + dc)
                    nr, nc = neighbour
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and neighbour not in seen
                        and grid[nr][nc] != 8
                    ):
                        seen.add(neighbour)
                        stack.append(neighbour)
            result.append(sorted(cells))
    return result


def priority_output(grid: list[list[int]], *, reverse: bool = False) -> list[list[int]]:
    """Independent mirror of the written rule, optionally reversing priority."""
    legend = [value for value in grid[0] if value not in (0, 8)]
    order = list(reversed(legend)) if reverse else legend
    output = deepcopy(grid)
    for room in chambers(grid):
        present = {grid[row][column] for row, column in room} & set(legend)
        winner = next((color for color in order if color in present), None)
        if winner is None:
            continue
        for row, column in room:
            output[row][column] = winner
    return output


def midpoint_rival(grid: list[list[int]]) -> list[list[int]]:
    """Old-family shortcut: ignore cyan connectivity and use four grid quadrants."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    legend = [value for value in grid[0] if value not in (0, 8)]
    output = deepcopy(grid)
    groups: dict[tuple[bool, bool], list[tuple[int, int]]] = {}
    for row in range(1, height):
        for column in range(width):
            if grid[row][column] != 8:
                groups.setdefault((row >= height // 2, column >= width // 2), []).append((row, column))
    for cells in groups.values():
        present = {grid[row][column] for row, column in cells} & set(legend)
        winner = next((color for color in legend if color in present), None)
        if winner is None:
            continue
        for row, column in cells:
            output[row][column] = winner
    return output


def room_bounds(grid: list[list[int]]) -> list[tuple[int, int, int, int]]:
    return [
        (min(r for r, _ in room), min(c for _, c in room),
         max(r for r, _ in room), max(c for _, c in room))
        for room in chambers(grid)
    ]


def layout_kind(grid: list[list[int]]) -> str:
    bounds = room_bounds(grid)
    row_spans = {(r1, r2) for r1, _, r2, _ in bounds}
    col_spans = {(c1, c2) for _, c1, _, c2 in bounds}
    if len(bounds) == 2 and len(row_spans) == 2 and len(col_spans) == 1:
        return "horizontal"
    if len(bounds) in (2, 3) and len(row_spans) == 1 and len(col_spans) == len(bounds):
        return "vertical"
    if len(bounds) == 4 and len(row_spans) == 2 and len(col_spans) == 2:
        return "grid"
    return "other"


def seed_pattern(grid: list[list[int]]) -> str:
    legend = set(grid[0][:3])
    counts = [sum(grid[r][c] in legend for r, c in room) for room in chambers(grid)]
    if counts and all(count == 1 for count in counts):
        return "single"
    if counts and all(count == 2 for count in counts):
        return "double"
    if counts and set(counts) == {1, 2}:
        return "mixed"
    return "other"


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout": layout_kind(grid),
        "seed_pattern": seed_pattern(grid),
    }


def is_midpoint_grid(grid: list[list[int]]) -> bool:
    bounds = room_bounds(grid)
    if layout_kind(grid) != "grid":
        return False
    row_starts = sorted({r1 for r1, _, _, _ in bounds})
    col_starts = sorted({c1 for _, c1, _, _ in bounds})
    divider_row = row_starts[1] - 1
    divider_col = col_starts[1] - 1
    return divider_row == len(grid) // 2 and divider_col == len(grid[0]) // 2
