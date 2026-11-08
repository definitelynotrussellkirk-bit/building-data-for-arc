"""Supplementary wrong rival; all four canonical pairs refute it."""


def solve(grid):
    result = [row[:] for row in grid]
    seeds = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 5)]
    for sr, sc, color in seeds:
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and (abs(r - sr) + abs(c - sc)) % 2 == 0:
                    result[r][c] = color
    return result
