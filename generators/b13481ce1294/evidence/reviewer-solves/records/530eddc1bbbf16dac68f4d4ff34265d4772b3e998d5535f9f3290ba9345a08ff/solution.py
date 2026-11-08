"""Visible-example solution for the blind ARC episode.

The input contains two equal-width panels separated by one vertical divider.
Keep a cell only when exactly one panel has a non-background value there.
"""


def solve(grid):
    if not grid or not grid[0]:
        return []

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if width % 2 != 1:
        raise ValueError("expected two equal panels with one separator column")

    separator = width // 2
    result = []
    for row in grid:
        left = row[:separator]
        right = row[separator + 1 :]
        result.append([
            a if a != 0 and b == 0 else b if b != 0 and a == 0 else 0
            for a, b in zip(left, right)
        ])
    return result
