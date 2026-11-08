"""Visible-example solution for task 297c05190f7c."""
from __future__ import annotations

from collections import deque


def solve(grid):
    """Fill the tight rectangle of each nonzero same-color 4-component."""
    height = len(grid)
    width = len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))

            rows = [row for row, _ in cells]
            cols = [col for _, col in cells]
            for row in range(min(rows), max(rows) + 1):
                for col in range(min(cols), max(cols) + 1):
                    output[row][col] = color

    return output
