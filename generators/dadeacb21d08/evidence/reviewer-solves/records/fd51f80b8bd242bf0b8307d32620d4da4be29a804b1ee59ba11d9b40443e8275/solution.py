"""Visible-example solution for dadeacb21d08."""
from __future__ import annotations


def solve(grid):
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            if len(component) == 3 and r1 - r0 == 1 and c1 - c0 == 1:
                for r in range(r0, r1 + 1):
                    for c in range(c0, c1 + 1):
                        out[r][c] = 3
    return out
