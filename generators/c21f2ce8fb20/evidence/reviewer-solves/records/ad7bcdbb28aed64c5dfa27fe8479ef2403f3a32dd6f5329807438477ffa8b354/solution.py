from collections import deque


def solve(grid):
    """Fill the 0/2 chamber containing the greatest number of red 2 cells."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    regions = []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] not in (0, 2):
                continue
            queue = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] not in (0, 2):
                        continue
                    seen.add((nr, nc))
                    queue.append((nr, nc))
            regions.append(cells)

    def score(cells):
        return sum(grid[r][c] == 2 for r, c in cells)

    winner = max(regions, key=score, default=[])
    out = [[0] * w for _ in range(h)]
    for r, c in winner:
        out[r][c] = 8
    return out
