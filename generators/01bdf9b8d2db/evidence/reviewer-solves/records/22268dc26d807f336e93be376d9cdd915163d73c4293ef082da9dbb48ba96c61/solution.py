from collections import deque


def solve(grid):
    """Fill each color-5-bounded chamber with its nonzero seed color."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] == 5:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            seed_colors = set()

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if grid[r][c] not in (0, 5):
                    seed_colors.add(grid[r][c])

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

            # Every demonstrated chamber has exactly one distinct seed color.
            # Leave an unsupported malformed chamber unchanged rather than guess.
            if len(seed_colors) == 1:
                fill_color = next(iter(seed_colors))
                for r, c in component:
                    out[r][c] = fill_color

    return out
