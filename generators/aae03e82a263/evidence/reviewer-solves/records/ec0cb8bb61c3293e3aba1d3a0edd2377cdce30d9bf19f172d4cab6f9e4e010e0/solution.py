"""Visible-example solution for aae03e82a263."""

from collections import deque


def solve(grid):
    """Extract the median-area 4-connected nonzero object and transpose it."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    seen = set()
    objects = []

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
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            objects.append((len(cells), color, cells))

    if not objects:
        return []

    objects.sort(key=lambda item: item[0])
    _, color, cells = objects[len(objects) // 2]
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)

    object_height = max_row - min_row + 1
    object_width = max_col - min_col + 1
    output = [[0 for _ in range(object_height)] for _ in range(object_width)]
    for row, col in cells:
        output[col - min_col][row - min_row] = color
    return output
