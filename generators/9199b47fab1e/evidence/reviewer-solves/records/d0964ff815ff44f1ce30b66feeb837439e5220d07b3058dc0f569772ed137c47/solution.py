"""Visible-only solution for task 9199b47fab1e."""

from collections import deque


def solve(grid):
    """Fill each seeded wall-bounded region with a 3/4/5 distance pattern.

    Cells colored 0 or 2 form the traversable regions.  A region is changed only
    when it contains at least one red (2) seed.  Its cells receive 3, 4, or 5
    according to the minimum Manhattan distance to a seed, modulo three.  All
    wall and exterior cells are preserved.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    result = [row[:] for row in grid]
    seen = [[False] * width for _ in range(height)]
    palette = (3, 4, 5)

    for start_r in range(height):
        for start_c in range(width):
            if seen[start_r][start_c] or grid[start_r][start_c] not in (0, 2):
                continue

            queue = deque([(start_r, start_c)])
            seen[start_r][start_c] = True
            component = []
            seeds = []

            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                if grid[r][c] == 2:
                    seeds.append((r, c))

                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and not seen[nr][nc]
                        and grid[nr][nc] in (0, 2)
                    ):
                        seen[nr][nc] = True
                        queue.append((nr, nc))

            if not seeds:
                continue

            for r, c in component:
                distance = min(abs(r - sr) + abs(c - sc) for sr, sc in seeds)
                result[r][c] = palette[distance % len(palette)]

    return result
