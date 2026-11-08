"""Infer seeded flood fill from the public demonstrations only."""

from collections import deque


def solve(grid):
    """Fill each seeded four-connected region, with color 5 as its walls."""
    result = [list(row) for row in grid]
    if not grid:
        return result
    height, width = len(grid), len(grid[0])
    visited = set()

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 5 or (row, col) in visited:
                continue
            queue = deque([(row, col)])
            visited.add((row, col))
            cells = []
            seed_colors = set()
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                if grid[r][c] != 0:
                    seed_colors.add(grid[r][c])
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (0 <= nr < height and 0 <= nc < width
                            and grid[nr][nc] != 5 and (nr, nc) not in visited):
                        visited.add((nr, nc))
                        queue.append((nr, nc))

            if len(seed_colors) > 1:
                raise ValueError("Multiple seed colors in one region are not specified by the examples")
            if seed_colors:
                color = next(iter(seed_colors))
                for r, c in cells:
                    result[r][c] = color
    return result
