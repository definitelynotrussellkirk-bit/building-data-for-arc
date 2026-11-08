"""Visible-example solution: retain the union of shortest-path predecessors."""
from collections import deque


def solve(grid):
    height, width = len(grid), len(grid[0])
    start = next((r, c) for r in range(height) for c in range(width) if grid[r][c] == 2)
    goal = next((r, c) for r in range(height) for c in range(width) if grid[r][c] == 3)
    distances = {start: 0}
    predecessors = {start: []}
    frontier = deque([start])
    while frontier:
        point = frontier.popleft()
        r, c = point
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            nr, nc = neighbor
            if not (0 <= nr < height and 0 <= nc < width) or grid[nr][nc] == 5:
                continue
            next_distance = distances[point] + 1
            if neighbor not in distances:
                distances[neighbor] = next_distance
                predecessors[neighbor] = [point]
                frontier.append(neighbor)
            elif distances[neighbor] == next_distance:
                predecessors[neighbor].append(point)
    result = [list(row) for row in grid]
    pending = [goal] if goal in distances else []
    visited = set()
    while pending:
        point = pending.pop()
        if point in visited:
            continue
        visited.add(point)
        r, c = point
        if grid[r][c] == 0:
            result[r][c] = 8
        pending.extend(predecessors[point])
    return result
