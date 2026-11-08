"""Visible-example solution for task 3233860e2d81."""
from collections import Counter


def solve(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    if len(ranked) < 3:
        raise ValueError("expected at least three non-background colors")
    return [[color] for color in ranked[:3]]
