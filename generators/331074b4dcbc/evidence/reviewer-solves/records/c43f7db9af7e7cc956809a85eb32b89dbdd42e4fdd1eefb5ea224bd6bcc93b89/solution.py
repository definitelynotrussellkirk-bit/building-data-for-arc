from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Replace the solid 8 rectangle with the repeating key from row 0."""
    out = [row[:] for row in grid]

    key: list[int] = []
    for value in grid[0]:
        if value == 0:
            break
        key.append(value)
    if not key:
        return out

    mask = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if r != 0 and value == 8
    ]
    if not mask:
        return out

    left = min(c for _, c in mask)
    for r, c in mask:
        out[r][c] = key[(c - left) % len(key)]
    return out
