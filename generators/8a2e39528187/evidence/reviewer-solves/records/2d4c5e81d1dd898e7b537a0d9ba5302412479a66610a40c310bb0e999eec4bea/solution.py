from collections import deque


def solve(grid):
    """Rank nonzero monochromatic objects by area, breaking ties by scan order."""
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]
    seen = [[False] * w for _ in range(h)]
    objects = []

    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] == 0 or seen[r0][c0]:
                continue
            color = grid[r0][c0]
            q = deque([(r0, c0)])
            seen[r0][c0] = True
            cells = []
            while q:
                r, c = q.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and grid[nr][nc] == color
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            objects.append(cells)

    objects.sort(key=lambda cells: (len(cells), min(cells)))
    for rank, cells in enumerate(objects, start=1):
        for r, c in cells:
            out[r][c] = 2 * rank
    return out
