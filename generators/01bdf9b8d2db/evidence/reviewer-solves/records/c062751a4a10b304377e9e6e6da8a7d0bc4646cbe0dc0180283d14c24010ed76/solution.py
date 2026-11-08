from collections import deque


def solve(grid):
    """Fill every non-5 chamber with its unique nonzero seed color."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    output = [row[:] for row in grid]
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

            # Visible examples give exactly one seed per chamber. Preserve an
            # unsupported chamber rather than guessing when that invariant fails.
            if len(seeds) == 1:
                fill = next(iter(seeds))
                for r, c in component:
                    output[r][c] = fill

    return output
