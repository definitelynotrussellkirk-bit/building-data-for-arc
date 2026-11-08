"""Visible-example solution for ARC task 135219aecdb4."""

from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Apply three synchronous row/column candidate-completion rounds.

    For each zero in the round's immutable snapshot, collect colors 1..4
    absent from both its row and column.  Fill only singleton candidate sets;
    leave ambiguous cells unchanged.  Three rounds are enough for the visible
    chains and preserve zeros when the examples do not justify a guess.
    """
    current = [row[:] for row in grid]
    colors = {1, 2, 3, 4}

    for _ in range(3):
        snapshot = [row[:] for row in current]
        updated = [row[:] for row in snapshot]
        changed = False

        for r in range(4):
            for c in range(4):
                if snapshot[r][c] != 0:
                    continue
                row_used = set(snapshot[r]) - {0}
                col_used = {snapshot[rr][c] for rr in range(4)} - {0}
                candidates = colors - row_used - col_used
                if len(candidates) == 1:
                    updated[r][c] = next(iter(candidates))
                    changed = True

        current = updated
        if not changed:
            break

    return current
