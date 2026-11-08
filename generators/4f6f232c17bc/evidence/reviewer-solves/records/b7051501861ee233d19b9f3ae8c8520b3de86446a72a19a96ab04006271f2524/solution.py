"""Visible-example solution for the blind ARC episode."""


def solve(grid):
    """Reflect the blue (1) object across the full gray (5) divider.

    The reflected object is recolored azure (8); cells falling outside the
    canvas are clipped.  The visible examples use a vertical divider, while
    the horizontal branch is the axis-symmetric extension of the same rule.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    vertical = [
        col
        for col in range(width)
        if all(grid[row][col] == 5 for row in range(height))
    ]
    horizontal = [
        row
        for row in range(height)
        if all(grid[row][col] == 5 for col in range(width))
    ]

    if len(vertical) == 1:
        axis = vertical[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == 1:
                    reflected_col = 2 * axis - col
                    if 0 <= reflected_col < width:
                        output[row][reflected_col] = 8
        return output

    if len(horizontal) == 1:
        axis = horizontal[0]
        for row in range(height):
            for col in range(width):
                if grid[row][col] == 1:
                    reflected_row = 2 * axis - row
                    if 0 <= reflected_row < height:
                        output[reflected_row][col] = 8
        return output

    raise ValueError("expected exactly one full gray divider row or column")
