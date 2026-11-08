"""Visible-example solution for task 0d1deab2505c."""
from __future__ import annotations

from collections import deque


BACKGROUND = 8
TAIL = 1
CENTER = 4
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
EIGHT = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)


def _component_of_ones(grid, start):
    """Return the 8-connected blue component containing start."""
    h, w = len(grid), len(grid[0])
    todo = deque([start])
    seen = {start}
    while todo:
        r, c = todo.popleft()
        for dr, dc in EIGHT:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] == TAIL
                and (nr, nc) not in seen
            ):
                seen.add((nr, nc))
                todo.append((nr, nc))
    return seen


def solve(grid):
    """Move each tailed cross to the wall opposite its tail and half-turn its arms."""
    h = len(grid)
    w = len(grid[0])
    creatures = []

    for cr in range(h):
        for cc in range(w):
            if grid[cr][cc] != CENTER:
                continue

            body = {(cr, cc)} | {(cr + dr, cc + dc) for dr, dc in CARDINAL}
            roots = []
            for dr, dc in CARDINAL:
                rr, rc = cr + 2 * dr, cc + 2 * dc
                if 0 <= rr < h and 0 <= rc < w and grid[rr][rc] == TAIL:
                    roots.append(((dr, dc), (rr, rc)))
            if len(roots) != 1:
                raise ValueError("each cross must have exactly one cardinal tail root")

            (tail_dr, tail_dc), root = roots[0]
            tail = _component_of_ones(grid, root)
            cells = body | tail
            min_r = min(r for r, _ in cells)
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)

            # The creature travels away from the tail until its full bounding box
            # touches the opposite wall. The tail translates without rotating.
            if (tail_dr, tail_dc) == (1, 0):       # tail below -> move upward
                shift = (-min_r, 0)
            elif (tail_dr, tail_dc) == (-1, 0):    # tail above -> move downward
                shift = (h - 1 - max_r, 0)
            elif (tail_dr, tail_dc) == (0, 1):     # tail right -> move left
                shift = (0, -min_c)
            else:                                  # tail left -> move right
                shift = (0, w - 1 - max_c)

            creatures.append(
                {
                    "center": (cr, cc),
                    "body": body,
                    "tail": tail,
                    "shift": shift,
                }
            )

    out = [row[:] for row in grid]
    for creature in creatures:
        for r, c in creature["body"] | creature["tail"]:
            out[r][c] = BACKGROUND

    for creature in creatures:
        cr, cc = creature["center"]
        sr, sc = creature["shift"]
        mr, mc = cr + sr, cc + sc

        for r, c in creature["tail"]:
            out[r + sr][c + sc] = TAIL
        out[mr][mc] = CENTER

        # A 180-degree body turn swaps each pair of opposite arm colors.
        for dr, dc in CARDINAL:
            out[mr + dr][mc + dc] = grid[cr - dr][cc - dc]

    return out
