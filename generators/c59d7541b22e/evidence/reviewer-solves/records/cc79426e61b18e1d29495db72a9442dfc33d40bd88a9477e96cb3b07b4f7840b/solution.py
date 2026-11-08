from copy import deepcopy


def solve(grid):
    """Complete every same-color three-of-four 2x2 window in one pass."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            cells = (
                (row, col),
                (row, col + 1),
                (row + 1, col),
                (row + 1, col + 1),
            )
            values = [grid[r][c] for r, c in cells]
            foreground = [value for value in values if value != 0]
            if len(foreground) == 3 and len(set(foreground)) == 1:
                missing = next(point for point, value in zip(cells, values) if value == 0)
                out[missing[0]][missing[1]] = foreground[0]
    return out
