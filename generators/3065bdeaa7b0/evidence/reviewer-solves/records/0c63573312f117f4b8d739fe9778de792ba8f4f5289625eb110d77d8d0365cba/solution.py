"""Visible-example solution for the prepared ARC episode."""
from __future__ import annotations

from collections import defaultdict


def _inclusive(a: int, b: int):
    step = 1 if a <= b else -1
    return range(a, b + step, step)


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Connect each color that occurs exactly twice with a row-first L path.

    Endpoints are ordered by (row, column).  Pair records are then processed in
    that same first-endpoint order, so a later path overwrites an earlier path at
    intersections.  Colors with counts other than two remain as input markers.
    """
    positions: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color != 0:
                positions[color].append((row_index, col_index))

    records: list[tuple[tuple[int, int], int, tuple[int, int]]] = []
    for color, points in positions.items():
        if len(points) == 2:
            first, second = sorted(points)
            records.append((first, color, second))
    records.sort(key=lambda record: record[0])

    output = [row[:] for row in grid]
    for first, color, second in records:
        for col_index in _inclusive(first[1], second[1]):
            output[first[0]][col_index] = color
        for row_index in _inclusive(first[0], second[0]):
            output[row_index][second[1]] = color
    return output
