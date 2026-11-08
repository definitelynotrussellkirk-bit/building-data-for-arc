"""Solve the visible ARC transformation for task 0832c700ffb9."""
from __future__ import annotations

from itertools import combinations
from typing import Sequence

Grid = list[list[int]]


def _paint_toward_midpoint(
    output: Grid,
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    """Paint color-5 guide dots every two cells from both endpoints."""
    r1, c1 = start
    r2, c2 = end

    if r1 == r2:
        if c1 > c2:
            c1, c2 = c2, c1
        midpoint_twice = c1 + c2
        column = c1 + 2
        while 2 * column <= midpoint_twice:
            output[r1][column] = 5
            column += 2
        column = c2 - 2
        while 2 * column >= midpoint_twice:
            output[r1][column] = 5
            column -= 2
        return

    if c1 == c2:
        if r1 > r2:
            r1, r2 = r2, r1
        midpoint_twice = r1 + r2
        row = r1 + 2
        while 2 * row <= midpoint_twice:
            output[row][c1] = 5
            row += 2
        row = r2 - 2
        while 2 * row >= midpoint_twice:
            output[row][c1] = 5
            row -= 2


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Expand each colored point and connect aligned point pairs.

    Each nonzero point becomes the center of a clipped 3x3 square.  Its center
    keeps its input color and its surrounding cells use the color of the other
    point in the same row.  Every pair of points sharing a row or column gets
    color-5 guide dots, spaced two cells apart and grown from both endpoints
    toward their midpoint.
    """
    if not grid or not grid[0]:
        return [list(row) for row in grid]

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    height = len(grid)
    output: Grid = [[0 for _ in range(width)] for _ in range(height)]
    points = [
        (row, column, int(value))
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value != 0
    ]

    for row, column, own_color in points:
        row_partners = [
            color
            for other_row, other_column, color in points
            if other_row == row and other_column != column
        ]
        if not row_partners:
            raise ValueError(f"point at ({row}, {column}) has no same-row partner")
        ring_color = row_partners[0]

        for rr in range(max(0, row - 1), min(height, row + 2)):
            for cc in range(max(0, column - 1), min(width, column + 2)):
                output[rr][cc] = ring_color
        output[row][column] = own_color

    for first, second in combinations(points, 2):
        r1, c1, _ = first
        r2, c2, _ = second
        if r1 == r2 or c1 == c2:
            _paint_toward_midpoint(output, (r1, c1), (r2, c2))

    return output
