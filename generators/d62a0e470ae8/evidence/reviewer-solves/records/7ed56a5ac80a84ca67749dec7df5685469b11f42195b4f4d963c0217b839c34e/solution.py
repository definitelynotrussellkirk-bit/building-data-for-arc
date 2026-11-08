"""Visible-example solution for d62a0e470ae8."""
from __future__ import annotations


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def solve(grid):
    key = grid[0][0]
    clean = [row[:] for row in grid]
    clean[0][0] = 0
    cells = max(_components(clean), key=len)
    r1 = min(r for r, _ in cells)
    r2 = max(r for r, _ in cells)
    c1 = min(c for _, c in cells)
    c2 = max(c for _, c in cells)
    crop = [row[c1 : c2 + 1] for row in clean[r1 : r2 + 1]]

    if key == 1:  # clockwise quarter-turn
        return [list(row) for row in zip(*crop[::-1])]
    if key == 2:  # left-right reflection
        return [row[::-1] for row in crop]
    if key == 3:  # top-bottom reflection
        return crop[::-1]
    if key == 4:  # half-turn
        return [row[::-1] for row in crop[::-1]]
    return crop
