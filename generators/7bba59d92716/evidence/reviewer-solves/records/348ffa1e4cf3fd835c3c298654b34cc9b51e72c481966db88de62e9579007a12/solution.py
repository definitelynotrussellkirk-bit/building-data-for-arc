"""Visible-example solution for task 7bba59d92716."""
from __future__ import annotations


def solve(grid):
    output = [row[:] for row in grid]
    if not grid:
        return output
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 1 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component = []
            while stack:
                row, col = stack.pop()
                component.append((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == 1
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(component) != 5:
                continue
            columns = {col for _, col in component}
            rows = sorted(row for row, _ in component)
            if len(columns) == 1 and rows == list(range(rows[0], rows[0] + 5)):
                output[rows[2]][next(iter(columns))] = 2

    return output
