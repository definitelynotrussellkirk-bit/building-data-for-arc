from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Recolor every orthogonal turn in each green path from 3 to 6."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 3:
                continue

            has_vertical = (
                (row > 0 and grid[row - 1][col] == 3)
                or (row + 1 < height and grid[row + 1][col] == 3)
            )
            has_horizontal = (
                (col > 0 and grid[row][col - 1] == 3)
                or (col + 1 < width and grid[row][col + 1] == 3)
            )

            if has_vertical and has_horizontal:
                out[row][col] = 6

    return out
