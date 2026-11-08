"""Visible-example solution for task 56072bfdb820."""
from __future__ import annotations

DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))


def _symbols(grid):
    symbols = []
    for tr in range(3):
        for tc in range(3):
            r0, c0 = tr * 4, tc * 4
            values = [
                grid[r0 + dr][c0 + dc]
                for dr in range(3)
                for dc in range(3)
                if grid[r0 + dr][c0 + dc] not in (6, 7)
            ]
            if values:
                symbols.append((tr, tc, values[0]))
    return symbols


def _put_diamond(grid, tr, tc, color):
    r0, c0 = tr * 4, tc * 4
    for dr, dc in DIAMOND:
        grid[r0 + dr][c0 + dc] = color


def solve(grid):
    symbols = _symbols(grid)
    if any(color != 2 for _, _, color in symbols):
        return [[7] * 16 for _ in range(16)]

    twos = [(row, col) for row, col, color in symbols if color == 2]
    if len(twos) != 2:
        raise ValueError("expected exactly two color-2 diamonds")
    (r1, c1), (r2, c2) = twos

    if c1 == c2:
        row, col = min(r1, r2) - 1, c1
        extras = ((row, col - 1, 5), (row, col + 1, 8))
    elif r1 == r2:
        row, col = r1, min(c1, c2) - 1
        extras = ((row - 1, col, 8), (row + 1, col, 5))
    elif c2 < c1:
        extras = ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    else:
        extras = ((r2, c2 + 1, 8), (r2 + 1, c2, 5))

    output = [list(row) for row in grid]
    occupied = {(row, col) for row, col, _ in symbols}
    for row, col, color in extras:
        if 0 <= row < 3 and 0 <= col < 3 and (row, col) not in occupied:
            _put_diamond(output, row, col, color)
    return output
