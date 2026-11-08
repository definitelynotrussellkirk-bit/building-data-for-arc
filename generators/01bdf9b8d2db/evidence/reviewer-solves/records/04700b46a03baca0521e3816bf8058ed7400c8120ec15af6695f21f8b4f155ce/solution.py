from collections import deque


def solve(grid):
    """Fill each non-5 connected compartment with its unique colored seed.

    Color 5 forms walls. Every 4-connected component of cells that are not 5
    contains one non-background seed color; the output propagates that color to
    every cell in the component while leaving the walls unchanged.
    """
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
            seeds = set()

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                value = grid[r][c]
                if value not in (0, 5):
                    seeds.add(value)

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

            # The visible examples consistently provide exactly one seed per
            # compartment. Keep an ambiguous component unchanged rather than
            # choosing an arbitrary color.
            if len(seeds) == 1:
                fill = next(iter(seeds))
                for r, c in component:
                    out[r][c] = fill

    return out
