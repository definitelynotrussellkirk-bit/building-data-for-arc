from collections import deque


def solve(grid):
    """Fill each region bounded by color 5 with the region's seed color."""
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or out[start_r][start_c] == 5:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            seed_colors = []

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                value = out[r][c]
                if value != 0:
                    seed_colors.append(value)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and out[nr][nc] != 5
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if seed_colors:
                fill = seed_colors[0]
                for r, c in component:
                    out[r][c] = fill

    return out
