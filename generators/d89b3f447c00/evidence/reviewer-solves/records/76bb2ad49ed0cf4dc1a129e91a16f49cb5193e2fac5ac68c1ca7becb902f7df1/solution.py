"""Visible-example solution: complete each same-color three-corner rectangle."""
from __future__ import annotations

from itertools import combinations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill missing fourth corners using only the original input cells."""
    output = [row[:] for row in grid]
    points: dict[int, set[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color:
                points.setdefault(color, set()).add((row_index, column_index))

    for color, cells in points.items():
        rows = sorted({row for row, _ in cells})
        columns = sorted({column for _, column in cells})
        for top, bottom in combinations(rows, 2):
            for left, right in combinations(columns, 2):
                corners = (
                    (top, left),
                    (top, right),
                    (bottom, left),
                    (bottom, right),
                )
                present = [corner for corner in corners if corner in cells]
                if len(present) == 3:
                    missing = next(corner for corner in corners if corner not in cells)
                    output[missing[0]][missing[1]] = color
    return output
