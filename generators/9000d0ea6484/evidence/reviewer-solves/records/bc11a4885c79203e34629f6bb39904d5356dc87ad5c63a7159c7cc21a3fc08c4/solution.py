"""Visible-example solution for the prepared ARC challenge."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Collapse four 4-column panels using the learned panel priority.

    Divider columns are 4, 9, and 14.  At each aligned (row, column), inspect
    panels in order third, fourth, first, second and return the first nonzero
    value; return zero if all four values are zero.
    """
    if not isinstance(grid, list) or len(grid) != 4:
        raise ValueError("expected a 4-row input")
    if any(not isinstance(row, list) or len(row) != 19 for row in grid):
        raise ValueError("expected a rectangular 4x19 input")

    starts = (0, 5, 10, 15)
    priority = (2, 3, 0, 1)
    output: list[list[int]] = []
    for row in range(4):
        out_row: list[int] = []
        for col in range(4):
            values = [grid[row][start + col] for start in starts]
            out_row.append(next((values[index] for index in priority if values[index]), 0))
        output.append(out_row)
    return output
