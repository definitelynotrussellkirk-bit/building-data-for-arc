"""Visible-example solution for b5df32f2dc17."""
from __future__ import annotations


def _runs(row: list[int]) -> list[tuple[int, int, int]]:
    """Return (original_index, color, length) for each nonzero row run."""
    found: list[tuple[int, int, int]] = []
    column = 0
    index = 0
    while column < len(row):
        if row[column] == 0:
            column += 1
            continue
        color = row[column]
        start = column
        while column < len(row) and row[column] == color:
            column += 1
        found.append((index, color, column - start))
        index += 1
    return found


def solve(grid: list[list[int]]) -> list[list[int]]:
    output: list[list[int]] = []
    for row in grid:
        ordered = sorted(_runs(row), key=lambda run: (-run[2], run[0]))
        rebuilt: list[int] = []
        for index, (_, color, length) in enumerate(ordered):
            if index:
                rebuilt.append(0)
            rebuilt.extend([color] * length)
        rebuilt.extend([0] * (len(row) - len(rebuilt)))
        output.append(rebuilt)
    return output
