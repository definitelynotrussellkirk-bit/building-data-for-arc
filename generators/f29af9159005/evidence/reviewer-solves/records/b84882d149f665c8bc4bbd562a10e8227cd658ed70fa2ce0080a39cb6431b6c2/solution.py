from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Draw a yellow cross through the single red cell, preserving markers."""
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
    for c, value in enumerate(grid[red_r]):
        if value == 0:
            out[red_r][c] = 4
    for r, row in enumerate(grid):
        if row[red_c] == 0:
            out[r][red_c] = 4
    return out
