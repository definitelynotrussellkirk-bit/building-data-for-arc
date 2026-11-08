from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Cast four yellow rays from the single red cell until blocked or at edge."""
    out = [row[:] for row in grid]
    red_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(red_cells) != 1:
        raise ValueError(f"expected exactly one red cell, found {len(red_cells)}")

    red_r, red_c = red_cells[0]
    height = len(grid)
    width = len(grid[0]) if height else 0
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        r, c = red_r + dr, red_c + dc
        while 0 <= r < height and 0 <= c < width:
            if grid[r][c] != 0:
                break
            out[r][c] = 4
            r += dr
            c += dc
    return out
