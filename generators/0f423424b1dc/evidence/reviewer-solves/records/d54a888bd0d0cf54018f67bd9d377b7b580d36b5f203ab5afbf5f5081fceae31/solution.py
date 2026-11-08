from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill only vertical spans whose two nonzero endpoints have one color."""
    if not grid:
        return []
    out = [row[:] for row in grid]
    height, width = len(grid), len(grid[0])
    for column in range(width):
        nonzero = [
            (row, grid[row][column])
            for row in range(height)
            if grid[row][column] != 0
        ]
        if len(nonzero) != 2 or nonzero[0][1] != nonzero[1][1]:
            continue
        top, color = nonzero[0]
        bottom = nonzero[1][0]
        for row in range(top, bottom + 1):
            out[row][column] = color
    return out
