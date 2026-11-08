"""Visible-example hypothesis: reflect blue cells across the gray column."""


def solve(grid):
    """Return a blank grid containing in-bounds reflections in color 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    if not height or not width or any(len(row) != width for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    axes = [column for column in range(width)
            if all(grid[row][column] == 5 for row in range(height))]
    if len(axes) != 1:
        raise ValueError("Expected exactly one full-height gray column")
    axis = axes[0]
    result = [[0] * width for _ in range(height)]
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 1:
                reflected = 2 * axis - column
                if 0 <= reflected < width:
                    result[row][reflected] = 8
    return result
