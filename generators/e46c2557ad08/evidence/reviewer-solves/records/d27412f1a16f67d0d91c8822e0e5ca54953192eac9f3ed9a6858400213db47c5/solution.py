"""Visible-example solution for the exposed e46c2557ad08 episode."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    """Recolor each exact horizontal two-cell gray component from 5 to 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = deepcopy(grid)
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 5 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component = set()
            while stack:
                row, col = stack.pop()
                component.add((row, col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if len(component) == 2:
                rows = {row for row, _ in component}
                cols = sorted(col for _, col in component)
                if len(rows) == 1 and cols[1] == cols[0] + 1:
                    for row, col in component:
                        output[row][col] = 8
    return output
