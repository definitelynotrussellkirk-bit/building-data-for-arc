"""Visible-example solution for the reviewer solve episode."""
from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replay every yellow offset around each red anchor on a blank canvas."""
    h = len(grid)
    w = len(grid[0]) if h else 0

    references = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(references) != 1:
        raise ValueError(f"expected one reference cell, found {len(references)}")
    rr, rc = references[0]

    offsets = [
        (r - rr, c - rc)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 4
    ]
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]

    output = [[0 for _ in range(w)] for _ in range(h)]
    for ar, ac in anchors:
        for dr, dc in offsets:
            r, c = ar + dr, ac + dc
            if 0 <= r < h and 0 <= c < w:
                output[r][c] = 4

    # Visible examples show red anchors survive even when a replay lands there.
    for r, c in anchors:
        output[r][c] = 2
    return output
