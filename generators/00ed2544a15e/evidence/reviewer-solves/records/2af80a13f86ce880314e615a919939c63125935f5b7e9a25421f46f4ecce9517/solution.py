from __future__ import annotations


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Join unobstructed orthogonally aligned red (2) cells with azure (8)."""
    if not grid:
        return []

    source = [row[:] for row in grid]
    result = [row[:] for row in grid]
    height = len(source)
    width = len(source[0])
    red = [(r, c) for r in range(height) for c in range(width) if source[r][c] == 2]

    for index, (r1, c1) in enumerate(red):
        for r2, c2 in red[index + 1 :]:
            if r1 == r2:
                left, right = sorted((c1, c2))
                between = range(left + 1, right)
                if all(source[r1][c] == 0 for c in between):
                    for c in range(left + 1, right):
                        result[r1][c] = 8
            elif c1 == c2:
                top, bottom = sorted((r1, r2))
                between = range(top + 1, bottom)
                if all(source[r][c1] == 0 for r in between):
                    for r in range(top + 1, bottom):
                        result[r][c1] = 8

    return result
