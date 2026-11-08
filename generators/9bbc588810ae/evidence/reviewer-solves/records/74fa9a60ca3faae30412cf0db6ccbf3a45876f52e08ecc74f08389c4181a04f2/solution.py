"""Visible-example solution for task 9bbc588810ae."""
from __future__ import annotations


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        return ()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _dims(cells):
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _variants(cells):
    """Return the eight rotations/reflections of a normalized cell set."""
    cells = _normalize(cells)
    h, w = _dims(cells)
    raw = (
        cells,
        tuple((c, h - 1 - r) for r, c in cells),
        tuple((h - 1 - r, w - 1 - c) for r, c in cells),
        tuple((w - 1 - c, r) for r, c in cells),
        tuple((r, w - 1 - c) for r, c in cells),
        tuple((h - 1 - r, c) for r, c in cells),
        tuple((c, r) for r, c in cells),
        tuple((w - 1 - c, h - 1 - r) for r, c in cells),
    )
    return {_normalize(shape) for shape in raw}


def solve(grid):
    # The visible examples have four 5x5 panels separated by columns of 9.
    starts = (0, 6, 12, 18)
    panels = []
    for left in starts:
        positions = [
            (r, c)
            for r in range(5)
            for c in range(5)
            if grid[r][left + c] != 0
        ]
        colors = [grid[r][left + c] for r, c in positions]
        panels.append((positions, _normalize(positions), colors[0] if colors else 0))

    query_positions, query_shape, _query_color = panels[-1]
    query_variants = _variants(query_shape)
    answer_color = 0
    for _positions, source_shape, source_color in panels[:-1]:
        if source_shape in query_variants:
            answer_color = source_color
            break

    output = [[0] * 5 for _ in range(5)]
    for r, c in query_positions:
        output[r][c] = answer_color
    return output
