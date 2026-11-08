from collections import deque


def solve(grid):
    result = [row[:] for row in grid]
    endpoints = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(endpoints) != 2:
        return result

    start, goal = endpoints
    queue = deque([start])
    parent = {start: None}
    height, width = len(grid), len(grid[0])

    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            nxt = (nr, nc)
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if nxt in parent or grid[nr][nc] not in (0, 2):
                continue
            parent[nxt] = (r, c)
            queue.append(nxt)

    if goal not in parent:
        return result

    current = goal
    while current is not None:
        r, c = current
        result[r][c] = 4
        current = parent[current]
    for r, c in endpoints:
        result[r][c] = 2
    return result
