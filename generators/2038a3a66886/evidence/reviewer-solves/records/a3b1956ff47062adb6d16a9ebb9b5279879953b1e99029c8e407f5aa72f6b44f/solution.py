"""Visible-example solution for task 2038a3a66886."""
from __future__ import annotations


def solve(grid):
    """Fill each horizontal span whose endpoints have the same nonzero color."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        positions = {}
        for c, color in enumerate(row):
            if color != 0:
                positions.setdefault(color, []).append(c)
        for color, columns in positions.items():
            if len(columns) >= 2:
                for c in range(columns[0], columns[-1] + 1):
                    out[r][c] = color
    return out
