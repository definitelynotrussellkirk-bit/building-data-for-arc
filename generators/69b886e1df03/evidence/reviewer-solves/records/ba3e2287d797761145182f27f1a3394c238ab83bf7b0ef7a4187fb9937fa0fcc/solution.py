from collections import deque


def solve(grid):
    """Complete each non-degenerate monochrome component's bounding rectangle."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            component = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [rr for rr, _ in component]
            cols = [cc for _, cc in component]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)

            # The examples leave one-cell-wide bars and singletons unchanged.
            if r0 == r1 or c0 == c1:
                continue

            for rr in range(r0, r1 + 1):
                for cc in range(c0, c1 + 1):
                    if out[rr][cc] == 0:
                        out[rr][cc] = color

    return out
