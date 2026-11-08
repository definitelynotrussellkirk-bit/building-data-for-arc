from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Copy the colored motif through a 180-degree rotation about the 9 cell."""
    out = [row[:] for row in grid]
    marker = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(marker) != 1:
        raise ValueError(f"expected exactly one color-9 pivot, found {len(marker)}")

    pr, pc = marker[0]
    height = len(grid)
    width = len(grid[0]) if height else 0

    for r, row in enumerate(grid):
        if len(row) != width:
            raise ValueError("grid must be rectangular")
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            rr = 2 * pr - r
            cc = 2 * pc - c
            if 0 <= rr < height and 0 <= cc < width:
                out[rr][cc] = value

    return out
