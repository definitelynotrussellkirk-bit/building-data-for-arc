from collections import deque


def solve(grid):
    """Recolor the center of each isolated 3-cell diagonal gray segment."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for r in range(height):
        for c in range(width):
            if grid[r][c] != 5 or (r, c) in seen:
                continue

            component = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                component.append((cr, cc))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] == 5
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            queue.append((nr, nc))

            if len(component) != 3:
                continue

            ordered = sorted(component)
            rows = [p[0] for p in ordered]
            cols = [p[1] for p in ordered]
            if rows[1] - rows[0] == rows[2] - rows[1] == 1:
                dc1 = cols[1] - cols[0]
                dc2 = cols[2] - cols[1]
                if dc1 == dc2 and abs(dc1) == 1:
                    mr, mc = ordered[1]
                    out[mr][mc] = 4

    return out
