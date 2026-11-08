from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill hollow monochrome cardinal-plus centers, preserving all other cells."""
    if not grid:
        return []
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            up = grid[row - 1][col]
            down = grid[row + 1][col]
            left = grid[row][col - 1]
            right = grid[row][col + 1]
            if up != 0 and up == down == left == right:
                out[row][col] = up
    return out
