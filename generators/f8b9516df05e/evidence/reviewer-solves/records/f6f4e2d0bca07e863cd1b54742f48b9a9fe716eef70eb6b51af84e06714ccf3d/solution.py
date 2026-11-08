"""Visible-example solution for the reviewer-authored episode."""
from copy import deepcopy


def solve(grid):
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        emitter = next((c for c, value in enumerate(row) if value not in (0, 8)), None)
        if emitter is None:
            continue
        blocker = next((c for c in range(emitter + 1, len(row)) if row[c] == 8), None)
        if blocker is None:
            continue
        color = row[emitter]
        for c in range(emitter + 1, blocker):
            out[r][c] = color
    return out
