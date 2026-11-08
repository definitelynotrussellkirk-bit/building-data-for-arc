from __future__ import annotations

from collections import deque
from typing import List


Grid = List[List[int]]


def _components(grid: Grid, color: int = 8) -> list[list[tuple[int, int]]]:
    """Return 4-connected components of ``color`` in row-major order."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    found: list[list[tuple[int, int]]] = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != color:
                        continue
                    seen.add(point)
                    queue.append(point)
            found.append(cells)
    return found


def solve(grid: Grid) -> Grid:
    """Recolor each azure component in its own bounding-box coordinate frame."""
    output = [row[:] for row in grid]

    for cells in _components(grid):
        top = min(row for row, _ in cells)
        bottom = max(row for row, _ in cells)
        left = min(col for _, col in cells)
        right = max(col for _, col in cells)
        height = bottom - top + 1
        width = right - left + 1

        for row, col in cells:
            local_row = row - top
            local_col = col - left
            left_half = 2 * local_col < width
            top_half = 2 * local_row < height

            if local_row < 2:
                output[row][col] = 6 if left_half else 1
            elif local_row >= height - 2:
                output[row][col] = 2 if left_half else 3
            elif local_col < 2:
                output[row][col] = 6 if top_half else 2
            elif local_col >= width - 2:
                output[row][col] = 1 if top_half else 3
            else:
                output[row][col] = 4

    return output
