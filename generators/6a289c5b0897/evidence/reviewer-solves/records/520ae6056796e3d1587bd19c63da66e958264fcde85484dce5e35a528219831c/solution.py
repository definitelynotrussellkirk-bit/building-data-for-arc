from __future__ import annotations

from collections import Counter, deque


def solve(grid):
    """Keep only the ordered BFS shortest path between the repeated terminals."""
    h = len(grid)
    w = len(grid[0])
    counts = Counter(value for row in grid for value in row if value not in (0, 5))
    endpoint_colors = sorted(color for color, count in counts.items() if count == 2)
    if not endpoint_colors:
        raise ValueError("expected one non-gray color appearing twice")
    color = endpoint_colors[0]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    start, goal = points[0], points[1]

    parent = {start: None}
    queue = deque([start])
    for_found = False
    while queue and not for_found:
        r, c = queue.popleft()
        if (r, c) == goal:
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if not (0 <= nr < h and 0 <= nc < w):
                continue
            if nxt in parent or grid[nr][nc] not in (0, color):
                continue
            parent[nxt] = (r, c)
            if nxt == goal:
                for_found = True
                break
            queue.append(nxt)

    if goal not in parent:
        raise ValueError("terminals are disconnected")
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = parent[current]

    out = [[0] * w for _ in range(h)]
    for r, c in path:
        out[r][c] = color
    return out
