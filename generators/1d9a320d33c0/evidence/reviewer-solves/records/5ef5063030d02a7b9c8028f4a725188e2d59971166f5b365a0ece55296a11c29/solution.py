"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations

from collections import deque


def _components(grid: list[list[int]]):
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            result.append((color, sorted(cells)))
    return result


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Complete every same-color domino into its orientation-directed 2x2."""
    output = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for color, cells in _components(grid):
        if len(cells) != 2:
            continue
        (row1, col1), (row2, col2) = cells
        if row1 == row2 and col2 == col1 + 1:
            target_row = row1 + 1
            if target_row < height:
                output[target_row][col1] = color
                output[target_row][col2] = color
        elif col1 == col2 and row2 == row1 + 1:
            target_col = col1 + 1
            if target_col < width:
                output[row1][target_col] = color
                output[row2][target_col] = color
    return output
