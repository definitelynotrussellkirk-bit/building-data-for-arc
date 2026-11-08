"""Example-derived solver. No repository imports or reference access."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("expected a nonempty grid")
    height, width = len(grid), len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("expected a rectangular grid")
    legend = [value for value in grid[0] if value != 0]
    if len(legend) != 3:
        raise ValueError("expected three legend colors")
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(seeds) != 1:
        raise ValueError("expected one seed")
    sr, sc = seeds[0]
    result = [row[:] for row in grid]
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == dc == 0:
                continue
            r, c, distance = sr + dr, sc + dc, 1
            while 0 <= r < height and 0 <= c < width and grid[r][c] != 1:
                if grid[r][c] == 0:
                    result[r][c] = legend[(distance - 1) % len(legend)]
                r += dr
                c += dc
                distance += 1
    return result
