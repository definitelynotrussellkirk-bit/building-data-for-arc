"""Visible-example solution for the prepared 3977ec54e4a0 episode.

Color-3 cells form one or more sparse chevron outlines.  Each chevron's
marker apex and diagonal arms determine a triangular wedge; paint the wedge
color 8 while preserving every color-3 marker and all cells outside wedges.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable

Grid = list[list[int]]
Point = tuple[int, int]


def _near(a: Point, b: Point) -> bool:
    """Connect nearby collinear/diagonal markers into one sparse outline."""
    dr = abs(a[0] - b[0])
    dc = abs(a[1] - b[1])
    return 0 < max(dr, dc) <= 2 and (dr == 0 or dc == 0 or dr == dc)


def _components(points: Iterable[Point]) -> list[set[Point]]:
    remaining = set(points)
    groups: list[set[Point]] = []
    while remaining:
        start = remaining.pop()
        group = {start}
        queue = deque([start])
        while queue:
            here = queue.popleft()
            joined = {p for p in remaining if _near(here, p)}
            remaining.difference_update(joined)
            group.update(joined)
            queue.extend(joined)
        groups.append(group)
    return groups


def _decode(component: set[Point]) -> tuple[Point, str, int]:
    """Return (apex, direction, depth) for a sparse chevron component."""
    candidates: list[tuple[int, Point, str]] = []
    for ar, ac in component:
        for direction in ("down", "up", "right", "left"):
            sides: set[int] = set()
            depth = 0
            valid = True
            for r, c in component:
                if direction == "down":
                    d, lateral = r - ar, c - ac
                elif direction == "up":
                    d, lateral = ar - r, c - ac
                elif direction == "right":
                    d, lateral = c - ac, r - ar
                else:
                    d, lateral = ac - c, r - ar

                if d < 0 or abs(lateral) != d:
                    valid = False
                    break
                if d:
                    sides.add(-1 if lateral < 0 else 1)
                    depth = max(depth, d)

            # A chevron has evidence on both arms.  Maximize depth only as a
            # deterministic tie-breaker; prepared examples yield one decoder.
            if valid and sides == {-1, 1} and depth > 0:
                candidates.append((depth, (ar, ac), direction))

    if not candidates:
        raise ValueError(f"could not decode marker component: {sorted(component)}")

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    depth, apex, direction = candidates[0]
    return apex, direction, depth


def _paint_wedge(out: Grid, apex: Point, direction: str, depth: int) -> None:
    h, w = len(out), len(out[0])
    ar, ac = apex
    for d in range(depth + 1):
        for lateral in range(-d, d + 1):
            if direction == "down":
                r, c = ar + d, ac + lateral
            elif direction == "up":
                r, c = ar - d, ac + lateral
            elif direction == "right":
                r, c = ar + lateral, ac + d
            else:
                r, c = ar + lateral, ac - d
            if 0 <= r < h and 0 <= c < w and out[r][c] != 3:
                out[r][c] = 8


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    markers = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    for component in _components(markers):
        apex, direction, depth = _decode(component)
        _paint_wedge(out, apex, direction, depth)
    return out
