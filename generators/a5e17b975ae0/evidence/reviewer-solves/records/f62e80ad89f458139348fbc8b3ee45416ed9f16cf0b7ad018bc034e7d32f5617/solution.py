from collections import deque


def solve(grid):
    """Fill each compartment containing a colored seed with that seed's color.

    Gray (9) frames and green (5) divider lines are walls.  The remaining cells
    form 4-connected compartments.  A compartment with exactly one non-wall,
    non-background color is painted with that color; unseeded compartments and
    the exterior stay unchanged.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    walls = {5, 9}

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] in walls:
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            seed_colors = set()

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                value = grid[r][c]
                if value != 0:
                    seed_colors.add(value)

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] not in walls
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if len(seed_colors) == 1:
                fill_color = next(iter(seed_colors))
                for r, c in component:
                    if grid[r][c] == 0:
                        out[r][c] = fill_color

    return out
