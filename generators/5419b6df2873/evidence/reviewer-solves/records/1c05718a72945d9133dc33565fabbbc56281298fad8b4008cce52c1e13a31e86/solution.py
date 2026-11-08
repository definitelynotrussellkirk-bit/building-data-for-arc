"""Visible-example solution for task 5419b6df2873."""


def solve(grid):
    """Extend each nonzero marker in the top row through its full column.

    The output starts blank, so non-marker cells below the top row are erased.
    """
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return []
    height = len(grid)
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return []

    output = [[0 for _ in range(width)] for _ in range(height)]
    for column, color in enumerate(grid[0]):
        if color != 0:
            for row in range(height):
                output[row][column] = color
    return output
