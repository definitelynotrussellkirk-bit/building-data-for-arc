from __future__ import annotations


def solve(grid):
    """Append a left-right reflection of each input row."""
    return [list(row) + list(reversed(row)) for row in grid]
