"""Visible-example solution for the chamber-fill puzzle."""
from collections import deque


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != 8
    }
    while remaining:
        start = next(iter(remaining))
        remaining.remove(start)
        queue = deque([start])
        component = [start]
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    queue.append(nxt)
                    component.append(nxt)
        colors = {grid[r][c] for r, c in component if grid[r][c] not in (0, 8)}
        if len(colors) != 1:
            raise ValueError(f"expected one seed color in chamber, found {sorted(colors)}")
        color = next(iter(colors))
        for r, c in component:
            out[r][c] = color
    return out
