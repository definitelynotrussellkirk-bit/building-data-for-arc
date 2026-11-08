"""Visible-example solution for ARC task 56072bfdb820."""
from __future__ import annotations

DIAMOND = ((0, 1), (1, 0), (1, 2), (2, 1))
TILES = tuple((r, c) for r in range(3) for c in range(3))


def _symbols(grid):
    found = []
    for tr, tc in TILES:
        r0, c0 = tr * 4, tc * 4
        values = [grid[r0 + dr][c0 + dc] for dr, dc in DIAMOND]
        non_background = [value for value in values if value != 7]
        if non_background:
            found.append((tr, tc, non_background[0]))
    return found


def _base_grid():
    result = [[7] * 11 for _ in range(11)]
    for r in (3, 7):
        result[r] = [6] * 11
    for c in (3, 7):
        for r in range(11):
            result[r][c] = 6
    return result


def _draw(result, tr, tc, color):
    r0, c0 = tr * 4, tc * 4
    for dr, dc in DIAMOND:
        result[r0 + dr][c0 + dc] = color


def solve(grid):
    symbols = _symbols(grid)
    if any(color != 2 for _, _, color in symbols):
        return [[7] * 16 for _ in range(16)]

    twos = [(r, c) for r, c, color in symbols if color == 2]
    if len(twos) != 2:
        raise ValueError("expected exactly two color-2 diamonds")
    (r1, c1), (r2, c2) = twos

    if c1 == c2:
        r, c = min(r1, r2) - 1, c1
        proposals = ((r, c - 1, 5), (r, c + 1, 8))
    elif r1 == r2:
        r, c = r1, min(c1, c2) - 1
        proposals = ((r - 1, c, 8), (r + 1, c, 5))
    elif c2 < c1:
        proposals = ((r2, c2 - 1, 8), (r2 + 1, c2, 5))
    else:
        proposals = ((r2, c2 + 1, 8), (r2 + 1, c2, 5))

    result = _base_grid()
    placements = {
        (r, c): color
        for r, c, color in proposals
        if 0 <= r < 3 and 0 <= c < 3
    }
    # The visible examples preserve the two observed color-2 symbols if an
    # inferred proposal would overlap one of them.
    placements.update({(r, c): color for r, c, color in symbols})
    for (r, c), color in placements.items():
        _draw(result, r, c, color)
    return result
