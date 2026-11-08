from __future__ import annotations

from typing import Sequence


def solve(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Extend the input vertically with two reflected traversals.

    The visible examples retain every input row in order, then reflect back to
    the first row, forward to the last row, and back to the first row again.
    For an input of height h this produces 4*h - 3 rows without duplicating a
    turning-point row.
    """
    rows = [list(row) for row in grid]
    if not rows:
        return []
    if len(rows) == 1:
        return [rows[0][:]]

    indices = (
        list(range(len(rows)))
        + list(range(len(rows) - 2, -1, -1))
        + list(range(1, len(rows)))
        + list(range(len(rows) - 2, -1, -1))
    )
    return [rows[index][:] for index in indices]
