from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Overlay the input with its main-diagonal transpose."""
    source = [row[:] for row in grid]
    output = [row[:] for row in source]
    for r, row in enumerate(source):
        for c, value in enumerate(row):
            if value != 0:
                output[c][r] = value
    return output
