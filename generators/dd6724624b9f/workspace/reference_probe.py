"""Independent Python diagnostics for dd6724624b9f.

This file is reviewer support, not label authority.  The selected Racket rule
remains authoritative; these helpers make task-local tests and future reviews
cheap and reproducible.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Iterable, Sequence

Grid = list[list[int]]
Cells = Iterable[tuple[int, int]]


def normalize(cells: Cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def transform(cells: Cells, code: int) -> tuple[tuple[int, int], ...]:
    cells = normalize(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    operations = {
        1: lambda r, c: (r, c),
        2: lambda r, c: (r, w - 1 - c),       # flip left/right
        3: lambda r, c: (h - 1 - r, c),       # flip up/down
        4: lambda r, c: (c, h - 1 - r),       # rotate clockwise
        5: lambda r, c: (h - 1 - r, w - 1 - c),
        6: lambda r, c: (w - 1 - c, r),       # rotate counter-clockwise
    }
    if code not in operations:
        raise ValueError(f"unsupported transform code {code}")
    return normalize(operations[code](r, c) for r, c in cells)


def legacy_transform(cells: Cells, code: int) -> tuple[tuple[int, int], ...]:
    """The stale five-code table shipped in the baseline generator."""
    cells = normalize(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    operations = {
        1: lambda r, c: (r, c),
        2: lambda r, c: (c, h - 1 - r),
        3: lambda r, c: (h - 1 - r, w - 1 - c),
        4: lambda r, c: (w - 1 - c, r),
        5: lambda r, c: (r, w - 1 - c),
        6: lambda r, c: (r, c),
    }
    return normalize(operations[code](r, c) for r, c in cells)


def components4(grid: Sequence[Sequence[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 0
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def body_cells(grid: Sequence[Sequence[int]]) -> tuple[tuple[int, int], ...]:
    work = deepcopy(grid)
    work[0][0] = 0
    work[0][1] = 0
    components = components4(work)
    if not components:
        raise ValueError("no body component")
    return normalize(max(components, key=len))


def oracle_output(grid: Sequence[Sequence[int]], *, legacy: bool = False,
                  preserve_body_color: bool = False) -> Grid:
    code = grid[0][0]
    out_color = grid[0][1]
    cells = body_cells(grid)
    transformed = legacy_transform(cells, code) if legacy else transform(cells, code)
    h = max(r for r, _ in transformed) + 1
    w = max(c for _, c in transformed) + 1
    if preserve_body_color:
        colors = [value for row in grid[2:] for value in row if value != 0]
        out_color = colors[0]
    out = [[0] * w for _ in range(h)]
    for r, c in transformed:
        out[r][c] = out_color
    return out
