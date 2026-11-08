"""Visible-example solution for the generated four-section overlay task."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay aligned 4-column sections in priority order 2, 3, 0, 1."""
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a non-empty list of rows")
    if any(not isinstance(row, list) or len(row) != 19 for row in grid):
        raise ValueError("expected a rectangular 19-column input")

    starts = (0, 5, 10, 15)
    priority = (2, 3, 0, 1)
    output: list[list[int]] = []
    for row in grid:
        out_row: list[int] = []
        for offset in range(4):
            value = 0
            for section in priority:
                candidate = row[starts[section] + offset]
                if candidate != 0:
                    value = candidate
                    break
            out_row.append(value)
        output.append(out_row)
    return output
