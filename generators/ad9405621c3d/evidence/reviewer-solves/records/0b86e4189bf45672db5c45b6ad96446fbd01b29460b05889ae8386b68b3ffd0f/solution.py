"""Visible-example solution for ad9405621c3d."""
from collections import deque


def solve(grid):
    h, w = len(grid), len(grid[0])
    by_color = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5):
                by_color.setdefault(value, []).append((r, c))
    pairs = [(color, cells) for color, cells in by_color.items() if len(cells) == 2]
    if len(pairs) != 1:
        return [row[:] for row in grid]
    color, (start, goal) = pairs[0]

    parent = {start: None}
    queue = deque([start])
    for_current = ((-1, 0), (1, 0), (0, -1), (0, 1))
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            break
        for dr, dc in for_current:
            nr, nc = r + dr, c + dc
            point = (nr, nc)
            if not (0 <= nr < h and 0 <= nc < w) or point in parent:
                continue
            if point != goal and grid[nr][nc] != 0:
                continue
            parent[point] = (r, c)
            queue.append(point)

    if goal not in parent:
        return [row[:] for row in grid]
    output = [row[:] for row in grid]
    current = goal
    while current is not None:
        r, c = current
        output[r][c] = color
        current = parent[current]
    return output
