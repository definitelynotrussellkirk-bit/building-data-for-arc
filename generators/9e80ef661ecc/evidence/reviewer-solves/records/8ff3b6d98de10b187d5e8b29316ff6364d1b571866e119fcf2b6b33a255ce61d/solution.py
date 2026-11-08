"""Visible-example solution for the reviewer-authored 9e80ef661ecc lesson."""
from __future__ import annotations

from collections import deque


def _objects(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = set()
            stack = [(r, c)]
            seen.add((r, c))
            while stack:
                rr, cc = stack.pop()
                cells.add((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _holes(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    r0, r1 = min(rows), max(rows)
    c0, c1 = min(cols), max(cols)
    blank = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if (r, c) not in cells
    }

    outside = set()
    queue = deque(
        point for point in blank
        if point[0] in (r0, r1) or point[1] in (c0, c1)
    )
    outside.update(queue)
    while queue:
        r, c = queue.popleft()
        for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if point in blank and point not in outside:
                outside.add(point)
                queue.append(point)

    enclosed = blank - outside
    count = 0
    while enclosed:
        count += 1
        start = enclosed.pop()
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in enclosed:
                    enclosed.remove(point)
                    stack.append(point)
    return count


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")
    out = [list(row) for row in grid]
    palette = {0: 2, 1: 3, 2: 4, 3: 6}
    for cells in _objects(grid):
        color = palette.get(_holes(cells), 9)
        for r, c in cells:
            out[r][c] = color
    return out
