"""Visible-example solution for the reflected-beam ARC lesson."""
from __future__ import annotations

from copy import deepcopy


def _reflect(direction: tuple[int, int], mirror: int) -> tuple[int, int]:
    dr, dc = direction
    if mirror == 1:      # slash: / 
        return -dc, -dr
    if mirror == 2:      # backslash: \
        return dc, dr
    raise ValueError(f"unsupported mirror color: {mirror}")


def solve(grid: list[list[int]]) -> list[list[int]]:
    if not grid or not grid[0]:
        return deepcopy(grid)
    h, w = len(grid), len(grid[0])

    # The examples contain one non-corner border marker whose color is neither
    # a mirror (1/2) nor a wall (5). It is the beam source and trail color.
    candidates: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if r not in (0, h - 1) and c not in (0, w - 1):
                continue
            value = grid[r][c]
            if value not in (0, 1, 2, 5):
                candidates.append((r, c))
    if len(candidates) != 1:
        raise ValueError(f"expected one border source, found {candidates}")

    sr, sc = candidates[0]
    color = grid[sr][sc]
    if sr == 0 and 0 < sc < w - 1:
        direction = (1, 0)
    elif sr == h - 1 and 0 < sc < w - 1:
        direction = (-1, 0)
    elif sc == 0 and 0 < sr < h - 1:
        direction = (0, 1)
    elif sc == w - 1 and 0 < sr < h - 1:
        direction = (0, -1)
    else:
        raise ValueError("source must be on a non-corner border cell")

    out = deepcopy(grid)
    r, c = sr + direction[0], sc + direction[1]
    seen_states: set[tuple[int, int, int, int]] = set()
    while 0 <= r < h and 0 <= c < w:
        state = (r, c, direction[0], direction[1])
        if state in seen_states:
            break
        seen_states.add(state)

        value = grid[r][c]  # trace against the original, not the painted output
        if value == 0:
            out[r][c] = color
        elif value == 5:
            break
        elif value in (1, 2):
            direction = _reflect(direction, value)
        else:
            break
        r += direction[0]
        c += direction[1]
    return out
