"""Visible-example solution for the exposed post-repair episode."""
from __future__ import annotations

from itertools import combinations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Turn exact color pairs into sorted color-8 span bars.

    Foreground colors that do not occur exactly twice are distractors.  For an
    exact pair, its length is the inclusive Chebyshev span between endpoints.
    """
    points: dict[int, list[tuple[int, int]]] = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                points.setdefault(value, []).append((row, col))

    lengths: list[int] = []
    for cells in points.values():
        if len(cells) != 2:
            continue
        first, second = cells
        lengths.append(
            max(abs(first[0] - second[0]), abs(first[1] - second[1])) + 1
        )

    if not lengths:
        return []
    lengths.sort()
    width = lengths[-1]
    return [[8] * length + [0] * (width - length) for length in lengths]
