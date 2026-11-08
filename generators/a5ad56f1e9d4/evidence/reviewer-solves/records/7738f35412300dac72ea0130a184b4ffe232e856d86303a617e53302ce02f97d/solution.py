"""Visible-example solution for a5ad56f1e9d4."""
from __future__ import annotations


def solve(grid):
    output = [row[:] for row in grid]
    markers = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]
    if len(markers) != 2:
        raise ValueError(f"expected two colored markers, found {len(markers)}")

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 5:
                continue
            nearest = min(
                markers,
                key=lambda marker: (
                    abs(row - marker[0]) + abs(col - marker[1]),
                    marker[2],
                    marker[0],
                    marker[1],
                ),
            )
            output[row][col] = nearest[2]
    return output
