"""Visible-example solution for the generated ARC episode."""
from __future__ import annotations

from collections import deque
from copy import deepcopy

Grid = list[list[int]]
Cell = tuple[int, int]
DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def components(grid: Grid, *, same_color: bool) -> list[tuple[Cell, list[Cell]]]:
    h, w = len(grid), len(grid[0])
    seen: set[Cell] = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            start = (r, c)
            color = grid[r][c]
            queue = deque([start])
            seen.add(start)
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in DIRS:
                    nr, nc = rr + dr, cc + dc
                    if not (0 <= nr < h and 0 <= nc < w) or (nr, nc) in seen:
                        continue
                    value = grid[nr][nc]
                    if value == 0 or (same_color and value != color):
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            cells.sort()
            result.append((start, cells))
    return result


def bounds(cells: list[Cell]) -> tuple[int, int, int, int]:
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def frames(grid: Grid) -> list[tuple[int, int, int, int]]:
    found = []
    for start, cells in components(grid, same_color=True):
        if grid[start[0]][start[1]] != 8:
            continue
        r1, c1, r2, c2 = bounds(cells)
        if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
            continue
        border = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if set(cells) == border:
            found.append((r1, c1, r2, c2))
    return sorted(found)


def loose_shapes(grid: Grid) -> list[tuple[int, int, tuple[tuple[int, ...], ...]]]:
    found = []
    for start, cells in components(grid, same_color=False):
        if grid[start[0]][start[1]] == 8:
            continue
        r1, c1, r2, c2 = bounds(cells)
        crop = tuple(
            tuple(grid[r][c] for c in range(c1, c2 + 1))
            for r in range(r1, r2 + 1)
        )
        found.append((r2 - r1 + 1, c2 - c1 + 1, crop))
    return found


def solve(grid: Grid) -> Grid:
    if not grid or not grid[0]:
        return deepcopy(grid)

    out = deepcopy(grid)
    shapes = loose_shapes(grid)
    used_values: list[tuple[int, int, tuple[tuple[int, ...], ...]]] = []

    for r1, c1, r2, c2 in frames(grid):
        inner_h, inner_w = r2 - r1 - 1, c2 - c1 - 1
        match = next(
            (
                shape
                for shape in shapes
                if shape[0] == inner_h
                and shape[1] == inner_w
                and shape not in used_values
            ),
            None,
        )
        if match is None:
            continue
        used_values.append(match)
        crop = match[2]
        for r, row in enumerate(crop):
            for c, value in enumerate(row):
                if value != 0:
                    out[r1 + 1 + r][c1 + 1 + c] = value
    return out
