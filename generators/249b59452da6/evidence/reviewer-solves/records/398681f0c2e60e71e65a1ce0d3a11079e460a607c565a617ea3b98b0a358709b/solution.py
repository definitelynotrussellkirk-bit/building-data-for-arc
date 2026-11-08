from copy import deepcopy


def solve(grid):
    """Complete empty corners of red diagonal pairs with green.

    For every 2x2 block in the *input* whose one diagonal is red (2, 2)
    and whose other diagonal is background (0, 0), recolor the two
    background corners green (3).  Other colors act as blockers and all
    original cells are preserved.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    result = deepcopy(grid)

    for row in range(height - 1):
        for col in range(width - 1):
            top_left = grid[row][col]
            top_right = grid[row][col + 1]
            bottom_left = grid[row + 1][col]
            bottom_right = grid[row + 1][col + 1]

            if top_left == 2 and bottom_right == 2 and top_right == 0 and bottom_left == 0:
                result[row][col + 1] = 3
                result[row + 1][col] = 3
            elif top_right == 2 and bottom_left == 2 and top_left == 0 and bottom_right == 0:
                result[row][col] = 3
                result[row + 1][col + 1] = 3

    return result
