"""Visible-example solution for task 96d4a788da47."""

from collections import deque


def solve(grid):
    """Slide every non-background 4-connected monochrome object to column 0.

    Each object's rows and internal geometry are preserved.  Objects are moved
    independently by subtracting their own minimum column from every cell.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            component = []
            queue = deque([(row, col)])
            seen.add((row, col))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            offset = min(c for _, c in component)
            for r, c in component:
                target = c - offset
                # The visible examples keep objects in disjoint row bands, so
                # independent left alignment cannot create a color conflict.
                out[r][target] = color

    return out
