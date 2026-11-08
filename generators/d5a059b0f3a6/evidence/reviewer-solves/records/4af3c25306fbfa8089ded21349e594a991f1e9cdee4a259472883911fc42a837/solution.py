"""Visible-example solver for the exposed d5a059b0f3a6 episode."""

from __future__ import annotations

from itertools import product
from typing import Iterable

Grid = list[list[int]]
Cell = tuple[int, int]


def _components(grid: Grid, color: int) -> list[set[Cell]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    out: list[set[Cell]] = []
    while unseen:
        start = unseen.pop()
        comp = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in unseen:
                    unseen.remove((rr, cc))
                    comp.add((rr, cc))
                    stack.append((rr, cc))
        out.append(comp)
    return out


def _corner_components(grid: Grid, frame_color: int) -> dict[str, list[Cell]]:
    """Return outer corner coordinates of the four possible 3-cell L shapes."""
    roles: dict[str, list[Cell]] = {k: [] for k in ("tl", "tr", "bl", "br")}
    for comp in _components(grid, frame_color):
        if len(comp) != 3:
            continue
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1 = min(rs), max(rs)
        c0, c1 = min(cs), max(cs)
        if r1 != r0 + 1 or c1 != c0 + 1:
            continue
        missing = ({(r, c) for r in (r0, r1) for c in (c0, c1)} - comp)
        if len(missing) != 1:
            continue
        miss = next(iter(missing))
        if miss == (r1, c1):
            roles["tl"].append((r0, c0))
        elif miss == (r1, c0):
            roles["tr"].append((r0, c1))
        elif miss == (r0, c1):
            roles["bl"].append((r1, c0))
        elif miss == (r0, c0):
            roles["br"].append((r1, c1))
    return roles


def _rectangles(grid: Grid, frame_color: int) -> list[tuple[int, int, int, int]]:
    roles = _corner_components(grid, frame_color)
    rects: list[tuple[int, int, int, int]] = []
    for tl, tr, bl, br in product(roles["tl"], roles["tr"], roles["bl"], roles["br"]):
        top, left = tl
        if tr[0] != top or bl[1] != left:
            continue
        right = tr[1]
        bottom = bl[0]
        if right <= left + 2 or bottom <= top + 2:
            continue
        if br != (bottom, right):
            continue
        rects.append((top, bottom, left, right))
    return sorted(set(rects))


def _one_sided(values: Iterable[int], axis_sum: int) -> bool:
    signs = [2 * value - axis_sum for value in values]
    return bool(signs) and (all(x <= 0 for x in signs) or all(x >= 0 for x in signs)) and any(x != 0 for x in signs)


def _choose_reflection(seed: set[Cell], rect: tuple[int, int, int, int]) -> set[Cell]:
    top, bottom, left, right = rect
    candidates: list[tuple[int, int, set[Cell]]] = []

    if _one_sided((r for r, _ in seed), top + bottom):
        reflected = {(top + bottom - r, c) for r, c in seed}
        # Prefer a true duplicated half over a reflection that mostly overlaps a centre line.
        candidates.append((len(reflected - seed), 0, reflected))

    if _one_sided((c for _, c in seed), left + right):
        reflected = {(r, left + right - c) for r, c in seed}
        candidates.append((len(reflected - seed), 1, reflected))

    if not candidates:
        return set(seed)
    # Visible examples make the intended axis the one adding the largest counterpart.
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    colors = {value for row in grid for value in row}
    frame_colors = sorted(colors - {0, 1})
    out = [[0 if value == 1 else value for value in row] for row in grid]

    for frame_color in frame_colors:
        for rect in _rectangles(grid, frame_color):
            top, bottom, left, right = rect
            seed = {
                (r, c)
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
                if grid[r][c] == 1
            }
            if not seed:
                continue
            completed = seed | _choose_reflection(seed, rect)
            for r, c in completed:
                out[r][c] = 1

    return out
