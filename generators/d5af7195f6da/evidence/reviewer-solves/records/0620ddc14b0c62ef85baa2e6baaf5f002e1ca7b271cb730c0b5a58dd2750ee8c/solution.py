"""Visible-example solution for d5af7195f6da."""
from collections import deque
from copy import deepcopy

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _distances(grid, start):
    h, w = len(grid), len(grid[0])
    distance = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIR4:
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and grid[nr][nc] != 5
                and (nr, nc) not in distance
            ):
                distance[(nr, nc)] = distance[(r, c)] + 1
                queue.append((nr, nc))
    return distance


def solve(grid):
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    maps = [(color, _distances(grid, (r, c))) for r, c, color in seeds]
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            reachable = [
                (dist[(r, c)], color)
                for color, dist in maps
                if (r, c) in dist
            ]
            if not reachable:
                continue
            best = min(distance for distance, _ in reachable)
            colors = {
                color for distance, color in reachable if distance == best
            }
            if len(colors) == 1:
                output[r][c] = next(iter(colors))
    return output
