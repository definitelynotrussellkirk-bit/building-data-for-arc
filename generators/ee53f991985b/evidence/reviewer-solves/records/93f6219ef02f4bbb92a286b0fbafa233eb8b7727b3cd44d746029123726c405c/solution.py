"""Visible-example solution for the prepared ee53f991985b episode."""
from __future__ import annotations


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            result.append((color, set(cells)))
    return result


def solve(grid):
    output = [list(row) for row in grid]
    for color, cells in _components(grid):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        row1, row2 = min(rows), max(rows)
        col1, col2 = min(cols), max(cols)
        border = {
            (row, col)
            for row in range(row1, row2 + 1)
            for col in range(col1, col2 + 1)
            if row in (row1, row2) or col in (col1, col2)
        }
        if cells != border:
            continue
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                output[row][col] = color
    return output
