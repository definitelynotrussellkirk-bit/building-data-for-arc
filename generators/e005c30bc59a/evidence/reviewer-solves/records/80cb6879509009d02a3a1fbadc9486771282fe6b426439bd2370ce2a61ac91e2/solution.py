"""Visible-example solution for the reflected-beam ARC task."""

from __future__ import annotations

from typing import List, Sequence, Tuple

Grid = List[List[int]]


def _find_source(grid: Sequence[Sequence[int]]) -> Tuple[int, int, int]:
    """Return the unique colored border emitter (row, column, color)."""
    h, w = len(grid), len(grid[0])
    candidates: list[Tuple[int, int, int]] = []
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 1, 2, 5) and (r in (0, h - 1) or c in (0, w - 1)):
                candidates.append((r, c, value))
    if len(candidates) != 1:
        raise ValueError(f"expected one border emitter, found {len(candidates)}")
    return candidates[0]


def _inward_direction(r: int, c: int, h: int, w: int) -> Tuple[int, int]:
    if r == 0:
        return 1, 0
    if r == h - 1:
        return -1, 0
    if c == 0:
        return 0, 1
    if c == w - 1:
        return 0, -1
    raise ValueError("emitter is not on the border")


def solve(grid: Grid) -> Grid:
    """Trace the emitter's beam, reflecting at 1/2 and stopping at 5/border."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be non-empty and rectangular")

    original = [row[:] for row in grid]
    output = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    r, c, color = _find_source(original)
    dr, dc = _inward_direction(r, c, h, w)

    # State includes direction: a crossing can revisit a cell legitimately, while
    # revisiting the same directed state proves the ray is in a mirror loop.
    seen: set[Tuple[int, int, int, int]] = set()
    while True:
        r += dr
        c += dc
        if not (0 <= r < h and 0 <= c < w):
            break

        state = (r, c, dr, dc)
        if state in seen:
            break
        seen.add(state)

        cell = original[r][c]
        if cell == 5:
            break
        if cell == 1:
            dr, dc = -dc, -dr
        elif cell == 2:
            dr, dc = dc, dr
        elif cell == 0:
            output[r][c] = color
        # Any pre-existing non-special colored cell is preserved and traversed.

    return output
