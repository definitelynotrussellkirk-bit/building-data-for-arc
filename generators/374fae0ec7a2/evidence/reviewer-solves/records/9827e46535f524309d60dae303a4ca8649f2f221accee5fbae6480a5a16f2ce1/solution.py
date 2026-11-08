"""Visible-example solution for task 374fae0ec7a2."""
from __future__ import annotations

from copy import deepcopy


DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    groups = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.pop(0)
                cells.append((rr, cc))
                for dr, dc in DIRS4:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            groups.append(cells)
    return groups


def _crop_binary(cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    shape = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        shape[r - r0][c - c0] = 1
    return shape


def _flip_lr(shape):
    return [row[::-1] for row in shape]


def _flip_ud(shape):
    return shape[::-1]


def _rot_cw(shape):
    return [list(row) for row in zip(*shape[::-1])]


def _rot_180(shape):
    return [row[::-1] for row in shape[::-1]]


def _rot_ccw(shape):
    return [list(row) for row in zip(*shape)][::-1]


def _apply(shape, code):
    if code == 1:
        return [row[:] for row in shape]
    if code == 2:
        return _flip_lr(shape)
    if code == 3:
        return _flip_ud(shape)
    if code == 4:
        return _rot_cw(shape)
    if code == 5:
        return _rot_180(shape)
    if code == 6:
        return _rot_ccw(shape)
    return [row[:] for row in shape]


def solve(grid):
    h, w = len(grid), len(grid[0])
    code1, code2 = grid[0][0], grid[0][1]

    work = deepcopy(grid)
    work[0][0] = 0
    work[0][1] = 0
    groups = _components(work)

    proto_cells = next(
        cells for cells in groups if any(work[r][c] == 9 for r, c in cells)
    )
    anchors = [
        cells[0]
        for cells in groups
        if len(cells) == 1 and cells is not proto_cells and work[cells[0][0]][cells[0][1]] != 9
    ]

    shape = _crop_binary(proto_cells)
    shape = _apply(shape, code1)
    shape = _apply(shape, code2)

    out = [[0] * w for _ in range(h)]
    sh, sw = len(shape), len(shape[0])
    for ar, ac in anchors:
        color = work[ar][ac]
        top = ar - sh // 2
        left = ac - sw // 2
        for r in range(sh):
            for c in range(sw):
                rr, cc = top + r, left + c
                if shape[r][c] and 0 <= rr < h and 0 <= cc < w:
                    out[rr][cc] = color
    return out
