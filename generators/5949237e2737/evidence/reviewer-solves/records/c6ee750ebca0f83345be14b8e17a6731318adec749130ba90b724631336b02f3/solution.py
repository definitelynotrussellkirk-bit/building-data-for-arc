"""Visible-example solution for task 5949237e2737."""


def solve(grid):
    """Keep only exact same-color mirror pairs, placing them on the right."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    divider = next(
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    )
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(divider):
            value = grid[row][col]
            mirror_col = 2 * divider - col
            if value != 0 and mirror_col < width and grid[row][mirror_col] == value:
                output[row][mirror_col] = value
    return output
