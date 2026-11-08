"""Visible-example solution for the transform-equivalence matrix puzzle."""
from __future__ import annotations


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _canonical_shape(panel):
    occupied = [
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not occupied:
        raise ValueError("empty panel")
    top = min(row for row, _ in occupied)
    bottom = max(row for row, _ in occupied)
    left = min(col for _, col in occupied)
    right = max(col for _, col in occupied)
    binary = [
        [1 if panel[row][col] != 0 else 0 for col in range(left, right + 1)]
        for row in range(top, bottom + 1)
    ]

    variants = []
    for start in (binary, _flip_lr(binary)):
        current = start
        for _ in range(4):
            variants.append(tuple(tuple(row) for row in current))
            current = _rotate_cw(current)
    return min(variants)


def _split_panels(grid):
    height = len(grid)
    width = len(grid[0])
    active = [any(grid[row][col] != 0 for row in range(height)) for col in range(width)]
    spans = []
    col = 0
    while col < width:
        while col < width and not active[col]:
            col += 1
        if col >= width:
            break
        start = col
        while col < width and active[col]:
            col += 1
        spans.append((start, col))
    return [[row[start:stop] for row in grid] for start, stop in spans]


def solve(grid):
    """Return the shape-equivalence matrix inferred from the visible examples."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be a non-empty rectangle")
    signatures = [_canonical_shape(panel) for panel in _split_panels(grid)]
    return [
        [5 if i == j else (2 if signatures[i] == signatures[j] else 0)
         for j in range(len(signatures))]
        for i in range(len(signatures))
    ]
