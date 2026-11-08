from collections import deque


def solve(grid):
    """Fill each region bounded by color 1 with its embedded marker color."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    height = len(grid)
    width = len(grid[0])
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] == 1:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            marker_colors = set()

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                value = grid[r][c]
                if value not in (0, 1):
                    marker_colors.add(value)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] != 1
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if len(marker_colors) == 1:
                fill_color = next(iter(marker_colors))
                for r, c in component:
                    out[r][c] = fill_color

    return out
