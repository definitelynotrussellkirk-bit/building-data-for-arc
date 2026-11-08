"""Visible-example solution for the post-repair ARC episode."""

from collections import deque


def solve(grid):
    """Rank the three nonzero 4-connected objects by area and recolor 2,3,4."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + dr
                    next_col = current_col + dc
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(cells)

    output = [[0 for _ in range(width)] for _ in range(height)]
    for rank, cells in enumerate(sorted(components, key=len)):
        for row, col in cells:
            output[row][col] = rank + 2
    return output
