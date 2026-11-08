from collections import deque


def solve(grid):
    """Fill every 4-connected zero region that cannot reach the border with 7."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 0 or seen[start_r][start_c]:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            touches_border = False

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if r == 0 or c == 0 or r == height - 1 or c == width - 1:
                    touches_border = True

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] == 0
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if not touches_border:
                for r, c in component:
                    out[r][c] = 7

    return out
