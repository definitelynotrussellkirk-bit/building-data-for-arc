"""Visible-example solution for task 52d56c2a0191."""
from __future__ import annotations


def solve(grid):
    """Return the sorted sizes of all 4-connected red (2) components."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    sizes = []
    for row in range(height):
        for column in range(width):
            if grid[row][column] != 2 or (row, column) in seen:
                continue
            stack = [(row, column)]
            seen.add((row, column))
            size = 0
            while stack:
                current_row, current_column = stack.pop()
                size += 1
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = current_row + dr, current_column + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            sizes.append(size)
    return [sorted(sizes)]
