from collections import deque


def solve(grid):
    """Color the two ends of each straight blue component orange."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 2 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 2
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = {r for r, _ in component}
            cols = {c for _, c in component}
            if len(rows) == 1:
                r = next(iter(rows))
                endpoints = [(r, min(c for _, c in component)), (r, max(c for _, c in component))]
            elif len(cols) == 1:
                c = next(iter(cols))
                endpoints = [(min(r for r, _ in component), c), (max(r for r, _ in component), c)]
            else:
                continue

            for r, c in endpoints:
                out[r][c] = 8

    return out
