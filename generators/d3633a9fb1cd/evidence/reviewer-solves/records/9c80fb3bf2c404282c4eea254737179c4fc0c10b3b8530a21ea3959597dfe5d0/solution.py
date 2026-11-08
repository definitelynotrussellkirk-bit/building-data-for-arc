from collections import deque


def _neighbors(r, c, h, w):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def _distances(grid, start):
    h, w = len(grid), len(grid[0])
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        for nr, nc in _neighbors(r, c, h, w):
            if grid[nr][nc] != 5 and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    return dist


def solve(grid):
    """Fill zeros from the unique nearest nonzero/non-5 seed through open cells."""
    out = [row[:] for row in grid]
    seeds = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 5)
    ]
    maps = [(color, _distances(grid, (r, c))) for r, c, color in seeds]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            candidates = [
                (distance[(r, c)], color)
                for color, distance in maps
                if (r, c) in distance
            ]
            if not candidates:
                continue
            best = min(distance for distance, _ in candidates)
            winners = {color for distance, color in candidates if distance == best}
            if len(winners) == 1:
                out[r][c] = next(iter(winners))
    return out
