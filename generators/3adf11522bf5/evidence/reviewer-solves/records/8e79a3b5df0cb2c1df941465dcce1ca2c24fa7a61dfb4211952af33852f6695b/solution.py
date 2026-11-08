from __future__ import annotations


def _empty_squares(grid):
    """Return ``(side, cells)`` for every all-zero axis-aligned square, side >= 2."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    squares = []
    for side in range(2, min(h, w) + 1):
        for r0 in range(h - side + 1):
            for c0 in range(w - side + 1):
                cells = {(r, c) for r in range(r0, r0 + side)
                         for c in range(c0, c0 + side)}
                if all(grid[r][c] == 0 for r, c in cells):
                    squares.append((side, cells))
    return squares


def solve(grid):
    """Paint the rule-selected empty squares with color 1.

    Find every largest all-zero square and paint the union of their cells.  Also
    paint each smaller all-zero square of side at least two that is completely
    disjoint from that largest-square union.  Nonzero obstacle cells never move.
    """
    out = [row[:] for row in grid]
    squares = _empty_squares(grid)
    if not squares:
        return out

    largest_side = max(side for side, _cells in squares)
    largest_union = set().union(
        *(cells for side, cells in squares if side == largest_side)
    )
    selected = set(largest_union)
    for _side, cells in squares:
        if cells.isdisjoint(largest_union):
            selected.update(cells)

    for r, c in selected:
        out[r][c] = 1
    return out
