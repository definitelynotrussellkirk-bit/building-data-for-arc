"""Visible-example solution for e0650802a8fb."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Fill qualifying same-color diagonal spans in first-appearance order."""
    output = [row[:] for row in grid]
    positions: dict[int, list[tuple[int, int]]] = {}
    order: list[int] = []
    for row_index, row in enumerate(grid):
        for col_index, color in enumerate(row):
            if color == 0:
                continue
            if color not in positions:
                positions[color] = []
                order.append(color)
            positions[color].append((row_index, col_index))

    for color in order:
        cells = positions[color]
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        dr, dc = r1 - r0, c1 - c0
        if dr == 0 or abs(dr) != abs(dc):
            continue
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1
        for step in range(abs(dr) + 1):
            output[r0 + step * step_r][c0 + step * step_c] = color
    return output
