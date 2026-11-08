"""Visible-example solution, written after earlier authoring exposure.

This file imports no project code and reads no files or labels.
"""
from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    visited = set()
    for r in range(h):
        for c in range(w):
            if not grid[r][c] or (r, c) in visited:
                continue
            component, stack = [], [(r, c)]
            visited.add((r, c))
            while stack:
                a, b = stack.pop()
                component.append((a, b))
                for da in (-1, 0, 1):
                    for db in (-1, 0, 1):
                        q = (a + da, b + db)
                        if (0 <= q[0] < h and 0 <= q[1] < w
                                and grid[q[0]][q[1]] and q not in visited):
                            visited.add(q)
                            stack.append(q)
            counts = Counter(grid[a][b] for a, b in component)
            main_color = max(counts, key=counts.get)
            shape = [(a, b) for a, b in component if grid[a][b] == main_color]
            top, bottom = min(a for a, _ in shape), max(a for a, _ in shape)
            left, right = min(b for _, b in shape), max(b for _, b in shape)
            for sr, sc in sorted(component):
                if grid[sr][sc] == main_color:
                    continue
                for a, b in shape:
                    nr = 2 * top - 1 - a if sr < top else 2 * bottom + 1 - a if sr > bottom else a
                    nc = 2 * left - 1 - b if sc < left else 2 * right + 1 - b if sc > right else b
                    if 0 <= nr < h and 0 <= nc < w:
                        result[nr][nc] = grid[sr][sc]
    return result
