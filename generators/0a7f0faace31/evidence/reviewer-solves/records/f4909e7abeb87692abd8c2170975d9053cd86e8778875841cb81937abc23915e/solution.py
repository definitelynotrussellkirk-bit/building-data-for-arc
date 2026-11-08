from __future__ import annotations

from collections import deque
from typing import Sequence

Grid = list[list[int]]


def _validated_grid(grid: Sequence[Sequence[int]]) -> Grid:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("grid must be a non-empty rectangular sequence")
    if not all(isinstance(row, (list, tuple)) and row for row in grid):
        raise ValueError("grid rows must be non-empty sequences")

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int for row in grid for value in row):
        raise TypeError("grid cells must be integers")

    return [list(row) for row in grid]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Return the first colored component centered inside the 7-marker box.

    Color 5 is the canvas and color 7 supplies sparse corner/edge markers.
    The markers' global bounding box defines a guide region.  Scan all other
    monochrome 4-connected components in row-major order; select the first
    component whose bounding-box midpoint lies inside the guide, then return
    the unmasked rectangular crop of that component's bounding box.
    """

    source = _validated_grid(grid)
    height, width = len(source), len(source[0])

    marker_cells = [
        (row, column)
        for row in range(height)
        for column in range(width)
        if source[row][column] == 7
    ]
    if not marker_cells:
        raise ValueError("grid contains no color-7 guide markers")

    guide_top = min(row for row, _ in marker_cells)
    guide_bottom = max(row for row, _ in marker_cells)
    guide_left = min(column for _, column in marker_cells)
    guide_right = max(column for _, column in marker_cells)

    visited: set[tuple[int, int]] = set()
    excluded = {5, 7}

    for start_row in range(height):
        for start_column in range(width):
            start = (start_row, start_column)
            color = source[start_row][start_column]
            if start in visited or color in excluded:
                continue

            queue = deque([start])
            visited.add(start)
            cells: list[tuple[int, int]] = []

            while queue:
                row, column = queue.popleft()
                cells.append((row, column))
                for next_row, next_column in (
                    (row - 1, column),
                    (row + 1, column),
                    (row, column - 1),
                    (row, column + 1),
                ):
                    next_cell = (next_row, next_column)
                    if not (0 <= next_row < height and 0 <= next_column < width):
                        continue
                    if next_cell in visited:
                        continue
                    if source[next_row][next_column] != color:
                        continue
                    visited.add(next_cell)
                    queue.append(next_cell)

            top = min(row for row, _ in cells)
            bottom = max(row for row, _ in cells)
            left = min(column for _, column in cells)
            right = max(column for _, column in cells)
            midpoint_row = (top + bottom) // 2
            midpoint_column = (left + right) // 2

            if (
                guide_top <= midpoint_row <= guide_bottom
                and guide_left <= midpoint_column <= guide_right
            ):
                return [
                    source[row][left : right + 1]
                    for row in range(top, bottom + 1)
                ]

    raise ValueError("no eligible colored component lies inside the guide")
