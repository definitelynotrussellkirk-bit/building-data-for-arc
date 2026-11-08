from copy import deepcopy


def solve(grid):
    """Complete empty corners of monochrome diagonal 2x2 pairs.

    A 2x2 window is changed only when one diagonal contains the same
    non-background color and both cells on the other diagonal are zero.
    Candidates are detected from the original grid and applied together so
    newly written cells cannot trigger a cascade.
    """
    source = [list(row) for row in grid]
    result = deepcopy(source)
    height = len(source)
    width = len(source[0]) if height else 0

    updates = {}
    for row in range(height - 1):
        for col in range(width - 1):
            top_left = source[row][col]
            top_right = source[row][col + 1]
            bottom_left = source[row + 1][col]
            bottom_right = source[row + 1][col + 1]

            if top_left != 0 and top_left == bottom_right and top_right == bottom_left == 0:
                updates[(row, col + 1)] = top_left
                updates[(row + 1, col)] = top_left
            elif top_right != 0 and top_right == bottom_left and top_left == bottom_right == 0:
                updates[(row, col)] = top_right
                updates[(row + 1, col + 1)] = top_right

    for (row, col), color in updates.items():
        result[row][col] = color
    return result
