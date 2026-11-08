"""Visible-example solution for f505996a2fdc."""
from __future__ import annotations


def _crop(grid):
    clean = [row[:] for row in grid]
    clean[0][0] = 0
    points = [
        (r, c)
        for r, row in enumerate(clean)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not points:
        return []
    r1 = min(r for r, _ in points)
    r2 = max(r for r, _ in points)
    c1 = min(c for _, c in points)
    c2 = max(c for _, c in points)
    return [row[c1 : c2 + 1] for row in clean[r1 : r2 + 1]]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [list(reversed(row)) for row in reversed(grid)]


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _flip_lr(grid):
    return [list(reversed(row)) for row in grid]


def _flip_ud(grid):
    return [row[:] for row in reversed(grid)]


def solve(grid):
    command = grid[0][0]
    motif = _crop(grid)
    transforms = {
        1: lambda value: [row[:] for row in value],
        2: _rotate_cw,
        3: _rotate_180,
        4: _transpose,
        5: _flip_lr,
        6: _flip_ud,
    }
    return transforms[command](motif)
