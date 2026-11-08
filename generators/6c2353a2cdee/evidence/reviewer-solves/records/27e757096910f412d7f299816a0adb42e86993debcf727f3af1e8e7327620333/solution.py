"""Visible-example solution for review episode 6c2353a2cdee."""
from __future__ import annotations


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid)][::-1]


def _transform(panel: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in panel]
    if code == 2:
        return _rotate_cw(panel)
    if code == 3:
        return [row[::-1] for row in panel[::-1]]
    if code == 4:
        return _rotate_ccw(panel)
    raise ValueError(f"unsupported visible code: {code}")


def solve(grid: list[list[int]]) -> list[list[int]]:
    if len(grid) != 7 or any(len(row) != 17 for row in grid):
        raise ValueError("expected the visible 7x17 three-panel layout")

    transformed: list[list[list[int]]] = []
    for left in (0, 6, 12):
        panel = [
            [1 if grid[row][left + col] else 0 for col in range(5)]
            for row in range(5)
        ]
        codes = [value for value in grid[6][left : left + 5] if value]
        if len(codes) != 1:
            raise ValueError("expected exactly one code below each panel")
        transformed.append(_transform(panel, codes[0]))

    colors = {0: 0, 1: 2, 2: 4, 3: 8}
    return [
        [
            colors[sum(panel[row][col] for panel in transformed)]
            for col in range(5)
        ]
        for row in range(5)
    ]
