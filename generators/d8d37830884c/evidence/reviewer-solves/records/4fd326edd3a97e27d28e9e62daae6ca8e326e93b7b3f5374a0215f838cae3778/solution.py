"""Visible-example solution for the generated component-size task."""
from __future__ import annotations


def solve(grid):
    """Recolor each same-color 4-connected object by its cell count.

    Objects containing exactly six cells become red (2); every other
    nonzero object becomes blue (1). Background cells remain zero.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list of rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            color = grid[start_row][start_col]
            if color == 0 or (start_row, start_col) in seen:
                continue

            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row, next_col = row + dr, col + dc
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        stack.append((next_row, next_col))

            replacement = 2 if len(cells) == 6 else 1
            for row, col in cells:
                output[row][col] = replacement

    return output
