"""Visible-only solution for the post-repair solve episode."""
from __future__ import annotations


def solve(grid):
    if not isinstance(grid, list) or not grid:
        return []
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    height = len(grid)
    output = [row[:] for row in grid]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 4 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            component = []
            while stack:
                row, col = stack.pop()
                component.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + dr, col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (
                        (next_row, next_col) not in seen
                        and grid[next_row][next_col] == 4
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            borders = set()
            if any(row == 0 for row, _ in component):
                borders.add("top")
            if any(row == height - 1 for row, _ in component):
                borders.add("bottom")
            if any(col == 0 for _, col in component):
                borders.add("left")
            if any(col == width - 1 for _, col in component):
                borders.add("right")

            if len(borders) == 2:
                for row, col in component:
                    output[row][col] = 8

    return output
