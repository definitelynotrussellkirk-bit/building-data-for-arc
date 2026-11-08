"""Visible-example solution for the prepared d1bf9a8e4c69 episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace each same-color 4-connected object by its bbox corners."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen: set[tuple[int, int]] = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            min_row = min(cell[0] for cell in cells)
            max_row = max(cell[0] for cell in cells)
            min_col = min(cell[1] for cell in cells)
            max_col = max(cell[1] for cell in cells)
            for corner_row, corner_col in (
                (min_row, min_col),
                (min_row, max_col),
                (max_row, min_col),
                (max_row, max_col),
            ):
                output[corner_row][corner_col] = color

    return output
