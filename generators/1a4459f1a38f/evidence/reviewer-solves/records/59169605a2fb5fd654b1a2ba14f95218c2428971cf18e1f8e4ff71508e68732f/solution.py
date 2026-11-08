"""Solution inferred from the final episode's visible examples only."""
from __future__ import annotations

from collections import deque


def solve(grid):
    """Crop the largest nonzero same-color 4-connected component."""
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and (next_row, next_col) not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add((next_row, next_col))
                        queue.append((next_row, next_col))
            components.append(cells)

    if not components:
        return [row[:] for row in grid]

    def choice_key(cells):
        top = min(row for row, _ in cells)
        left = min(col for _, col in cells)
        return (-len(cells), top, left)

    selected = min(components, key=choice_key)
    top = min(row for row, _ in selected)
    bottom = max(row for row, _ in selected)
    left = min(col for _, col in selected)
    right = max(col for _, col in selected)
    return [row[left : right + 1] for row in grid[top : bottom + 1]]
