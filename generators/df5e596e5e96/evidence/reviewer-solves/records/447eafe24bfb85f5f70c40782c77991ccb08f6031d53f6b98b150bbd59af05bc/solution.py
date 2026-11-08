"""Visible-example solution for the blind ARC episode.

The input is five square panels separated by one blank column.  Each panel
contains one monochrome shape.  The output is the pairwise relationship matrix:
8 on the diagonal, 1 for translation-equivalent shapes, 2 for a non-trivial
rotation, 3 for a reflection (possibly followed by rotation), and 0 otherwise.
"""

from __future__ import annotations


def _normalize(points: set[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    if not points:
        return frozenset()
    min_r = min(r for r, _ in points)
    min_c = min(c for _, c in points)
    return frozenset((r - min_r, c - min_c) for r, c in points)


def _rotate_clockwise(
    points: frozenset[tuple[int, int]],
) -> frozenset[tuple[int, int]]:
    return _normalize({(c, -r) for r, c in points})


def _rotations(
    points: frozenset[tuple[int, int]],
) -> tuple[frozenset[tuple[int, int]], ...]:
    variants = [points]
    for _ in range(3):
        variants.append(_rotate_clockwise(variants[-1]))
    return tuple(variants)


def _reflect(points: frozenset[tuple[int, int]]) -> frozenset[tuple[int, int]]:
    return _normalize({(r, -c) for r, c in points})


def _relationship(
    left: frozenset[tuple[int, int]],
    right: frozenset[tuple[int, int]],
) -> int:
    if left == right:
        return 1
    if right in _rotations(left)[1:]:
        return 2
    if right in _rotations(_reflect(left)):
        return 3
    return 0


def solve(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    if height == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be non-empty and rectangular")

    # Visible examples use N square HxH panels and one separator column between
    # consecutive panels: W = N*H + (N-1).
    panel_count, remainder = divmod(width + 1, height + 1)
    if panel_count <= 0 or remainder:
        raise ValueError("input does not have square panels separated by one column")

    shapes: list[frozenset[tuple[int, int]]] = []
    for panel_index in range(panel_count):
        start_col = panel_index * (height + 1)
        points = {
            (r, c)
            for r in range(height)
            for c in range(height)
            if grid[r][start_col + c] != 0
        }
        shapes.append(_normalize(points))

    return [
        [
            8 if row_index == col_index else _relationship(shapes[row_index], shapes[col_index])
            for col_index in range(panel_count)
        ]
        for row_index in range(panel_count)
    ]
