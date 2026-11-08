"""Visible-example solution for the prepared ARC challenge."""

from __future__ import annotations

from typing import Iterable, List, Sequence

Grid = List[List[int]]


def _rotate_clockwise(matrix: Sequence[Sequence[int]]) -> Grid:
    """Return a rectangular binary matrix rotated 90 degrees clockwise."""
    return [list(row) for row in zip(*matrix[::-1])]


def solve(grid: Sequence[Sequence[int]]) -> Grid:
    """Move the gray shape into the colored frame after a clockwise turn.

    The gray object's bounding-box mask is rotated clockwise, its source cells
    are erased, and the rotated mask is stamped with its top-left cell at the
    frame's top-left interior corner.  The stamp is authoritative, so a gray
    cell may replace a frame-border cell when the rotated shape reaches it.
    """
    rows = len(grid)
    cols = len(grid[0]) if rows else 0
    out = [list(row) for row in grid]

    gray = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 3]
    if not gray:
        return out

    r0 = min(r for r, _ in gray)
    r1 = max(r for r, _ in gray)
    c0 = min(c for _, c in gray)
    c1 = max(c for _, c in gray)
    mask = [
        [1 if grid[r][c] == 3 else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]
    rotated = _rotate_clockwise(mask)

    frame_cells = [
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if grid[r][c] not in (0, 3)
    ]
    if not frame_cells:
        raise ValueError("visible rule requires one non-gray colored frame")
    frame_top = min(r for r, _ in frame_cells)
    frame_left = min(c for _, c in frame_cells)

    for r, c in gray:
        out[r][c] = 0

    anchor_r = frame_top + 1
    anchor_c = frame_left + 1
    for dr, row in enumerate(rotated):
        for dc, occupied in enumerate(row):
            if occupied:
                rr = anchor_r + dr
                cc = anchor_c + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    out[rr][cc] = 3

    return out


# Common harness aliases.
transform = solve
solution = solve
