"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations

from typing import Sequence

Grid = list[list[int]]


def _solid_3x3_origins(grid: Sequence[Sequence[int]]) -> list[tuple[int, int]]:
    height = len(grid)
    width = len(grid[0])
    return [
        (row, col)
        for row in range(height - 2)
        for col in range(width - 2)
        if all(grid[row + dr][col + dc] != 0 for dr in range(3) for dc in range(3))
    ]


def _axis_slot(coordinates: list[int]) -> int:
    """Decode top/middle/bottom (or left/middle/right) from glyph extent."""
    low, high = min(coordinates), max(coordinates)
    if high == 1:
        return 0
    if low == 1:
        return 2
    return 1


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Pack each colored 3x3 direction glyph into its decoded compass slot."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")

    output = [[5 for _ in range(9)] for _ in range(9)]
    origins = _solid_3x3_origins(grid)
    if len(origins) != 9:
        raise ValueError(f"expected nine solid 3x3 tiles, found {len(origins)}")

    for top, left in origins:
        colored = [
            (dr, dc)
            for dr in range(3)
            for dc in range(3)
            if grid[top + dr][left + dc] != 5
        ]
        if not colored:  # the all-gray tile represents the untouched center
            continue
        target_row = _axis_slot([dr for dr, _ in colored])
        target_col = _axis_slot([dc for _, dc in colored])
        for dr in range(3):
            for dc in range(3):
                output[3 * target_row + dr][3 * target_col + dc] = grid[top + dr][left + dc]
    return output
