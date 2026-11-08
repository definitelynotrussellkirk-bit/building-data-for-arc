from __future__ import annotations

from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Fill qualifying marker columns into top-down color bands.

    A column qualifies exactly when its last nonzero cell is color 5.  Reading
    the nonzero marker cells from top to bottom, each marker's color fills the
    rows after the preceding marker through that marker.  Cells below the last
    marker and all nonqualifying columns are left unchanged.
    """
    if not grid:
        return []

    output = [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])

    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    for col in range(width):
        markers = [(row, int(grid[row][col])) for row in range(height) if grid[row][col] != 0]
        if not markers or markers[-1][1] != 5:
            continue

        start = 0
        for stop, color in markers:
            for row in range(start, stop + 1):
                output[row][col] = color
            start = stop + 1

    return output
