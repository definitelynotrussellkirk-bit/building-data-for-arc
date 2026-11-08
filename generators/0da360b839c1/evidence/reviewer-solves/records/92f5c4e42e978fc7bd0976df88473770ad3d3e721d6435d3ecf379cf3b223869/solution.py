from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Rotate every non-background cell 180 degrees about the unique 9 pivot."""
    height = len(grid)
    width = len(grid[0])
    pivot = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    pr, pc = pivot

    result = [[0 for _ in range(width)] for _ in range(height)]
    result[pr][pc] = 9
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            rr = 2 * pr - r
            cc = 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                result[rr][cc] = value
    return result
