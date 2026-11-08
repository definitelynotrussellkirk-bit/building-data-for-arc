"""Visible-example solution for task 70b9864c90a3."""

from __future__ import annotations

from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Fill a zero cell whose four diagonal neighbors share one nonzero color.

    All predicates are evaluated against the original input, so newly filled cells
    cannot trigger additional fills.
    """
    source = [list(row) for row in grid]
    if not source:
        return []

    width = len(source[0])
    if any(len(row) != width for row in source):
        raise ValueError("grid must be rectangular")

    result = [row[:] for row in source]
    for row in range(1, len(source) - 1):
        for col in range(1, width - 1):
            if source[row][col] != 0:
                continue
            color = source[row - 1][col - 1]
            if color == 0:
                continue
            if (
                source[row - 1][col + 1] == color
                and source[row + 1][col - 1] == color
                and source[row + 1][col + 1] == color
            ):
                result[row][col] = color
    return result
