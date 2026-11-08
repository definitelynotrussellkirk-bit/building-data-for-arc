from __future__ import annotations

from collections import deque
from typing import List

Grid = List[List[int]]


def _components_of_nine(grid: Grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 9}
    components = []
    while unseen:
        start = unseen.pop()
        comp = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    comp.add((nr, nc))
                    queue.append((nr, nc))
        components.append(comp)
    return components


def _crop_nonzero(grid: Grid) -> Grid:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        return []
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def _rotate_cw(tile: Grid) -> Grid:
    return [list(row) for row in zip(*tile[::-1])]


def _transform(tile: Grid, code: int) -> Grid:
    if code == 5:
        return [row[:] for row in tile]
    if code == 6:
        return _rotate_cw(tile)
    if code == 7:
        return [row[::-1] for row in tile]
    raise ValueError(f"unsupported visible transform code: {code}")


def solve(grid: Grid) -> Grid:
    h, w = len(grid), len(grid[0])

    # Each connected color-9 component is the border of one gallery frame.
    gallery = {}
    for comp in _components_of_nine(grid):
        r0 = min(r for r, _ in comp)
        r1 = max(r for r, _ in comp)
        c0 = min(c for _, c in comp)
        c1 = max(c for _, c in comp)
        if r1 - r0 < 2 or c1 - c0 < 2:
            continue
        center_col = (c0 + c1) // 2
        if r0 == 0:
            continue
        key = grid[r0 - 1][center_col]
        if key == 0 or key == 9:
            continue
        interior = [row[c0 + 1 : c1] for row in grid[r0 + 1 : r1]]
        gallery[key] = _crop_nonzero(interior)

    # The last two rows encode ordered (gallery-key, transform-code) pairs.
    program = [
        (grid[h - 2][c], grid[h - 1][c])
        for c in range(w)
        if grid[h - 2][c] != 0 and grid[h - 1][c] != 0
    ]
    tiles = [_transform(gallery[key], code) for key, code in program]
    if not tiles:
        return []

    out_h = max(len(tile) for tile in tiles)
    out_w = sum(len(tile[0]) for tile in tiles) + len(tiles) - 1
    out = [[0] * out_w for _ in range(out_h)]
    offset = 0
    for index, tile in enumerate(tiles):
        for r, row in enumerate(tile):
            out[r][offset : offset + len(row)] = row
        offset += len(tile[0])
        if index + 1 < len(tiles):
            offset += 1
    return out
