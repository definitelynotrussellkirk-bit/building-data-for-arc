from collections import deque


def solve(grid):
    """Fill each 5-bounded region that contains exactly one marker color."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] == 5:
                continue

            component = []
            colors = set()
            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                value = grid[r][c]
                if value != 0:
                    colors.add(value)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != 5
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if len(colors) == 1:
                fill = next(iter(colors))
                for r, c in component:
                    out[r][c] = fill

    return out
