from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Keep the four corners of every solid monochrome 3x3 block."""
    if not grid:
        return []
    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    for row in range(height - 2):
        for col in range(width - 2):
            color = grid[row][col]
            if color == 0:
                continue
            if all(
                grid[r][c] == color
                for r in range(row, row + 3)
                for c in range(col, col + 3)
            ):
                out[row][col] = color
                out[row][col + 2] = color
                out[row + 2][col] = color
                out[row + 2][col + 2] = color

    return out
