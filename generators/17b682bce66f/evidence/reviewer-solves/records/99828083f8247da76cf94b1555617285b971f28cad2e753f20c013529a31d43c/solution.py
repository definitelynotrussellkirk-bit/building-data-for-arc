from __future__ import annotations


def _rotate_clockwise(dr: int, dc: int, turns: int) -> tuple[int, int]:
    for _ in range(turns % 4):
        dr, dc = dc, -dr
    return dr, dc


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Stamp rotated copies of the 8-template around colored marker cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width:
        return [row[:] for row in grid]

    pivots = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(pivots) != 1:
        return [row[:] for row in grid]
    pivot_r, pivot_c = pivots[0]

    template = [
        (r - pivot_r, c - pivot_c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    markers = sorted(
        (value, r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 2 <= value <= 5
    )

    result = [row[:] for row in grid]
    for r, row in enumerate(result):
        for c, value in enumerate(row):
            if value in (8, 9):
                row[c] = 0

    for marker, center_r, center_c in markers:
        turns = marker - 2
        paint = marker + 2
        for dr, dc in template:
            rr, cc = _rotate_clockwise(dr, dc, turns)
            target_r = center_r + rr
            target_c = center_c + cc
            if 0 <= target_r < height and 0 <= target_c < width:
                result[target_r][target_c] = paint

    return result
