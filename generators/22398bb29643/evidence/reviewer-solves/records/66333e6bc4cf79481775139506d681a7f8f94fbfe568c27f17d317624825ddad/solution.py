"""Visible-example solution for the repaired task 22398bb29643."""
from collections import deque


def solve(grid):
    """List component colors by bounding-box top row, then left column."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    components = []

    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
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
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen or grid[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            components.append(cells)

    components.sort(
        key=lambda cells: (
            min(row for row, _ in cells),
            min(col for _, col in cells),
        )
    )
    return [[grid[min(cells)[0]][min(cells)[1]] for cells in components]]
