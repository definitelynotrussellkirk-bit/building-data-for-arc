from __future__ import annotations

from copy import deepcopy
from typing import Any


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Preserve the unique top-row marker and erase its colour below row 0."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    markers = [(column, value) for column, value in enumerate(grid[0]) if value != 0]
    if len(markers) != 1:
        raise ValueError("expected exactly one nonzero marker in the top row")
    _, marker_colour = markers[0]
    output = deepcopy(grid)
    for row in range(1, len(output)):
        for column in range(len(output[0])):
            if output[row][column] == marker_colour:
                output[row][column] = 0
    return output
