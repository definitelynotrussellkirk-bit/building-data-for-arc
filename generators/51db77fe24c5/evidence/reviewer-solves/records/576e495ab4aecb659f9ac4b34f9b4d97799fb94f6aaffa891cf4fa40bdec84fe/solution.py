from collections import deque


def solve(grid):
    """Recolor each isolated solid 2x2 component from 1 to 2."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] != 1 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = {r for r, _ in component}
            cols = {c for _, c in component}
            if len(component) == 4 and len(rows) == 2 and len(cols) == 2:
                for r, c in component:
                    out[r][c] = 2

    return out
