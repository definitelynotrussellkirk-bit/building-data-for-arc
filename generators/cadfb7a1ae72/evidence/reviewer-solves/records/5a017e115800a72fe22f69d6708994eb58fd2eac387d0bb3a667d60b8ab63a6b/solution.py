from __future__ import annotations

from collections import deque

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            seen.add((r, c))
            queue = deque([(r, c)])
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            r0 = min(rr for rr, _ in cells)
            c0 = min(cc for _, cc in cells)
            normalized = {(rr - r0, cc - c0) for rr, cc in cells}
            found.append((r0, c0, normalized))
    found.sort(key=lambda item: (item[0], item[1]))
    return [shape for _, _, shape in found]


def _symmetry_class(shape):
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    row_symmetric = all((height - 1 - r, c) in shape for r, c in shape)
    column_symmetric = all((r, width - 1 - c) in shape for r, c in shape)
    return int(row_symmetric) + 2 * int(column_symmetric)


def _hole_count(shape):
    height = max(r for r, _ in shape) + 1
    width = max(c for _, c in shape) + 1
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if (r, c) not in shape
    }
    holes = 0
    while remaining:
        start = remaining.pop()
        queue = deque([start])
        touches_border = False
        while queue:
            r, c = queue.popleft()
            if r in (0, height - 1) or c in (0, width - 1):
                touches_border = True
            for dr, dc in _CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
        if not touches_border:
            holes += 1
    return holes


def solve(grid):
    shapes = _objects(grid)
    features = [(_symmetry_class(shape), _hole_count(shape)) for shape in shapes]
    n = len(features)
    return [
        [
            1
            if i == j
            else 8
            if features[i][0] == features[j][0]
            else 4
            if features[i][1] == features[j][1]
            else 0
            for j in range(n)
        ]
        for i in range(n)
    ]
