"""Visible-example-only solution for the blind ARC task."""


def solve(grid):
    """Fill the empty midpoint between equal-colored diagonal endpoints.

    The endpoints must be exactly two rows and two columns apart.  Existing
    nonzero cells are never overwritten, and newly filled cells do not create
    additional candidates within the same solve.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    # Use only the original nonzero cells as endpoints.  Checking the two
    # downward diagonals visits each unordered endpoint pair once.
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for dcol in (-2, 2):
                other_row = row + 2
                other_col = col + dcol
                if not (0 <= other_row < height and 0 <= other_col < width):
                    continue
                if grid[other_row][other_col] != color:
                    continue
                mid_row = row + 1
                mid_col = col + dcol // 2
                if grid[mid_row][mid_col] == 0:
                    out[mid_row][mid_col] = color

    return out
