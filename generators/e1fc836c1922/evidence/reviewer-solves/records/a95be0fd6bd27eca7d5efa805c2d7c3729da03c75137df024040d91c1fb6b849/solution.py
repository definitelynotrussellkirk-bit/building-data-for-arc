from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Preserve the input and copy each nonzero cell across the main diagonal."""
    out = [row[:] for row in grid]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                out[col][row] = value
    return out
