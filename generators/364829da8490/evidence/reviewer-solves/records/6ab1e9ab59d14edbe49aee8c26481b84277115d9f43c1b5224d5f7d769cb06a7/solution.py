from collections import deque
from copy import deepcopy

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def solve(grid):
    """Fill each enclosed 4-connected zero region with its sole boundary color."""
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] != 0 or (start_row, start_col) in seen:
                continue

            queue = deque([(start_row, start_col)])
            seen.add((start_row, start_col))
            cells = []
            boundary_colors = set()
            touches_border = False

            while queue:
                row, col = queue.popleft()
                cells.append((row, col))
                if row in (0, height - 1) or col in (0, width - 1):
                    touches_border = True

                for delta_row, delta_col in _CARDINAL:
                    next_row = row + delta_row
                    next_col = col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    value = grid[next_row][next_col]
                    if value == 0:
                        if (next_row, next_col) not in seen:
                            seen.add((next_row, next_col))
                            queue.append((next_row, next_col))
                    else:
                        boundary_colors.add(value)

            if not touches_border and len(boundary_colors) == 1:
                fill = next(iter(boundary_colors))
                for row, col in cells:
                    output[row][col] = fill

    return output
