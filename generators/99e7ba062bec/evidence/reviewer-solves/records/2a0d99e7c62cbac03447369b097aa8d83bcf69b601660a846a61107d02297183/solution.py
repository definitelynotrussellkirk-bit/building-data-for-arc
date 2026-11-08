"""Visible-example solution for the three-panel transform analogy."""
from __future__ import annotations


def _crop(grid: list[list[int]]) -> list[list[int]]:
    rows = [r for r, row in enumerate(grid) if any(value != 0 for value in row)]
    cols = [
        c
        for c in range(len(grid[0]))
        if any(grid[r][c] != 0 for r in range(len(grid)))
    ]
    if not rows or not cols:
        return []
    return [
        row[min(cols) : max(cols) + 1]
        for row in grid[min(rows) : max(rows) + 1]
    ]


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    """Split on one-or-more columns that are zero in every row."""
    width = len(grid[0])
    occupied = [any(row[col] != 0 for row in grid) for col in range(width)]
    panels: list[list[list[int]]] = []
    start: int | None = None
    for col, active in enumerate(occupied + [False]):
        if active and start is None:
            start = col
        elif not active and start is not None:
            panels.append(_crop([row[start:col] for row in grid]))
            start = None
    if len(panels) != 3:
        raise ValueError(f"expected exactly three panels, found {len(panels)}")
    return panels


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*grid[::-1])]


def _rotate_180(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid[::-1]]


def _rotate_ccw(grid: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*grid)][::-1]


def _flip_lr(grid: list[list[int]]) -> list[list[int]]:
    return [row[::-1] for row in grid]


def _flip_ud(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid[::-1]]


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(column) for column in zip(*grid)]


_TRANSFORMS = (
    _identity,
    _rotate_cw,
    _rotate_180,
    _rotate_ccw,
    _flip_lr,
    _flip_ud,
    _transpose,
)


def _mask(grid: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in grid]


def solve(grid: list[list[int]]) -> list[list[int]]:
    panel_a, panel_b, panel_c = _split_panels(grid)
    a_mask = _mask(panel_a)
    b_mask = _mask(panel_b)
    for transform in _TRANSFORMS:
        if _crop(transform(a_mask)) == b_mask:
            return _crop(transform(panel_c))
    raise ValueError("no supported geometric transform maps panel A to panel B")
