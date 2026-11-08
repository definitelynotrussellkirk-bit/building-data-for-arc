"""Visible-example solution for the post-repair reviewer episode."""
from __future__ import annotations


def _step_if_far(delta: int) -> int:
    """Return one signed step only when the target is more than one cell away."""
    if delta > 1:
        return 1
    if delta < -1:
        return -1
    return 0


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Move the central 9 coarsely toward 6 and relabel the target as 9."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    marker = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    target = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6]
    if len(marker) != 1 or len(target) != 1:
        raise ValueError("expected exactly one color-9 marker and one color-6 target")

    mr, mc = marker[0]
    tr, tc = target[0]
    nr = mr + _step_if_far(tr - mr)
    nc = mc + _step_if_far(tc - mc)

    out = [row[:] for row in grid]
    out[mr][mc] = 5
    out[nr][nc] = 9
    out[tr][tc] = 9
    return out
