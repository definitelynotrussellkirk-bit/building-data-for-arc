"""Visible-example solver for fd277c567993."""
from __future__ import annotations

from typing import Sequence

Grid = list[list[int]]


def _split(grid: Sequence[Sequence[int]]) -> tuple[Grid, Grid, Grid]:
    if not grid or not grid[0]:
        raise ValueError("empty grid")
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("ragged grid")
    separators = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(separators) != 2:
        raise ValueError(f"expected two full-height color-5 separators, got {separators}")
    a, b = separators
    return tuple(
        [list(row[lo:hi]) for row in grid]
        for lo, hi in ((0, a), (a + 1, b), (b + 1, w))
    )  # type: ignore[return-value]


def _anchor(panel: Sequence[Sequence[int]]) -> tuple[int, int]:
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not cells:
        raise ValueError("panel has no object")
    return min(r for r, _ in cells), min(c for _, c in cells)


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    before, after, query = _split(grid)
    before_top, before_left = _anchor(before)
    query_top, query_left = _anchor(query)

    offsets = [
        (r - before_top, c - before_left)
        for r, row in enumerate(after)
        for c, value in enumerate(row)
        if value == 8 and before[r][c] != 8
    ]

    out = [row[:] for row in query]
    for dr, dc in offsets:
        r, c = query_top + dr, query_left + dc
        if not (0 <= r < len(out) and 0 <= c < len(out[0])):
            raise ValueError("translated marker is out of bounds")
        out[r][c] = 8
    return out
