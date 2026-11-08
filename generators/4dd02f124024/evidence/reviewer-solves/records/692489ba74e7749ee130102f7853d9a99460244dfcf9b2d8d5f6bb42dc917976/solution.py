"""Visible-example solution for ARC task 4dd02f124024."""

from __future__ import annotations

from typing import Iterable, Sequence

Grid = list[list[int]]
Frame = tuple[int, int, int, int, int]


def _uniform_frames(grid: Sequence[Sequence[int]]) -> Iterable[Frame]:
    """Yield every nonzero, one-cell-thick rectangular frame in scan order."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    for top in range(height - 2):
        for left in range(width - 2):
            color = grid[top][left]
            if color == 0:
                continue
            for bottom in range(top + 2, height):
                if grid[bottom][left] != color:
                    continue
                for right in range(left + 2, width):
                    if grid[top][right] != color or grid[bottom][right] != color:
                        continue
                    if not all(grid[top][col] == color for col in range(left, right + 1)):
                        continue
                    if not all(grid[bottom][col] == color for col in range(left, right + 1)):
                        continue
                    if not all(grid[row][left] == color for row in range(top, bottom + 1)):
                        continue
                    if not all(grid[row][right] == color for row in range(top, bottom + 1)):
                        continue
                    yield top, left, bottom, right, color


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Erase a frame's occupied interior when any interior color is foreign."""
    if not grid:
        return []
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    source = [list(row) for row in grid]
    result = [row[:] for row in source]

    for top, left, bottom, right, frame_color in _uniform_frames(source):
        occupied = [
            result[row][col]
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
            if result[row][col] != 0
        ]
        if occupied and any(color != frame_color for color in occupied):
            for row in range(top + 1, bottom):
                for col in range(left + 1, right):
                    if result[row][col] != 0:
                        result[row][col] = 0

    return result
