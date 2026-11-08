from collections import deque


def solve(grid):
    """Fill every background region enclosed by a single nonzero color."""
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
            region = []
            boundary_colors = set()
            touches_edge = False

            while queue:
                r, c = queue.popleft()
                region.append((r, c))
                if r in (0, height - 1) or c in (0, width - 1):
                    touches_edge = True

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    value = grid[nr][nc]
                    if value == 0:
                        if not seen[nr][nc]:
                            seen[nr][nc] = True
                            queue.append((nr, nc))
                    else:
                        boundary_colors.add(value)

            if not touches_edge and len(boundary_colors) == 1:
                fill = next(iter(boundary_colors))
                for r, c in region:
                    out[r][c] = fill

    return out
