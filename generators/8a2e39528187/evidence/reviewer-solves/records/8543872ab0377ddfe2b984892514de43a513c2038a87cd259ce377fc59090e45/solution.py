from collections import deque


def solve(grid):
    """Recolour each 4-connected nonzero object according to its area.

    The visible examples consistently map areas 2, 3, 4, and 5 to colours
    2, 4, 6, and 8 respectively, while preserving every occupied cell.
    """
    h = len(grid)
    w = len(grid[0]) if h else 0
    out = [row[:] for row in grid]
    seen = [[False] * w for _ in range(h)]

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
            new_color = 2 * (len(cells) - 1)
            for r, c in cells:
                out[r][c] = new_color
    return out
