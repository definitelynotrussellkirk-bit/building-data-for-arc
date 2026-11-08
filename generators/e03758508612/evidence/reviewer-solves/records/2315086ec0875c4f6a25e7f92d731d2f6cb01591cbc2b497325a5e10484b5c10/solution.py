"""Visible-only solver for the prepared chamber-priority puzzle."""
from __future__ import annotations

from copy import deepcopy


def solve(grid):
    if not grid or not grid[0]:
        return deepcopy(grid)

    height = len(grid)
    width = len(grid[0])
    priority = [value for value in grid[0] if value not in (0, 8)]
    output = deepcopy(grid)
    seen = set()
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    for row in range(1, height):
        for column in range(width):
            start = (row, column)
            if start in seen or grid[row][column] == 8:
                continue

            stack = [start]
            seen.add(start)
            chamber = []
            while stack:
                current_row, current_column = stack.pop()
                chamber.append((current_row, current_column))
                for delta_row, delta_column in directions:
                    next_row = current_row + delta_row
                    next_column = current_column + delta_column
                    next_cell = (next_row, next_column)
                    if (
                        1 <= next_row < height
                        and 0 <= next_column < width
                        and next_cell not in seen
                        and grid[next_row][next_column] != 8
                    ):
                        seen.add(next_cell)
                        stack.append(next_cell)

            present = {grid[r][c] for r, c in chamber}
            winner = next((color for color in priority if color in present), None)
            if winner is not None:
                for chamber_row, chamber_column in chamber:
                    output[chamber_row][chamber_column] = winner

    return output
