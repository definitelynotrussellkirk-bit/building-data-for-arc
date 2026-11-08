from copy import deepcopy


def solve(grid):
    """Recolor every clear blue endpoint span, including endpoints, red."""
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0

    # Detect all eligible pairs in the unchanged input.  Using the original
    # cells matters when a horizontal and vertical span cross.
    horizontal = []
    for row in range(height):
        columns = [column for column in range(width) if grid[row][column] == 1]
        for left, right in zip(columns, columns[1:]):
            if right - left > 1 and all(
                grid[row][column] == 0 for column in range(left + 1, right)
            ):
                horizontal.append((row, left, right))

    vertical = []
    for column in range(width):
        rows = [row for row in range(height) if grid[row][column] == 1]
        for top, bottom in zip(rows, rows[1:]):
            if bottom - top > 1 and all(
                grid[row][column] == 0 for row in range(top + 1, bottom)
            ):
                vertical.append((column, top, bottom))

    for row, left, right in horizontal:
        for column in range(left, right + 1):
            output[row][column] = 2
    for column, top, bottom in vertical:
        for row in range(top, bottom + 1):
            output[row][column] = 2
    return output
