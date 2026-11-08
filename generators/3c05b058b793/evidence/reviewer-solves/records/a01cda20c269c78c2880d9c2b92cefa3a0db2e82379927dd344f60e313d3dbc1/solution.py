from collections import deque


def _distances(grid, start):
    h, w = len(grid), len(grid[0])
    inf = h * w + 1
    dist = [[inf] * w for _ in range(h)]
    q = deque([start])
    dist[start[0]][start[1]] = 0
    while q:
        r, c = q.popleft()
        nd = dist[r][c] + 1
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != 5 and nd < dist[nr][nc]:
                dist[nr][nc] = nd
                q.append((nr, nc))
    return dist


def solve(grid):
    red = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2)
    green = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
    d_red = _distances(grid, red)
    d_green = _distances(grid, green)

    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (2, 3, 5):
                continue
            if d_red[r][c] < d_green[r][c]:
                out[r][c] = 8
            elif d_green[r][c] < d_red[r][c]:
                out[r][c] = 4
            else:
                out[r][c] = 0
    return out
