"""Solve by ranking isolated colored components by bounding-box height."""
from __future__ import annotations


def solve(grid):
    rows = len(grid)
    cols = len(grid[0])
    seen = set()
    objects = []

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            top = min(rr for rr, _ in cells)
            bottom = max(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            height = bottom - top + 1
            objects.append((height, left, color))

    objects.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [[color for _, _, color in objects]]
