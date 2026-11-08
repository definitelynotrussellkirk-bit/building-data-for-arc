"""Visible-example solution for blind task 0a54983176e5."""


def solve(grid):
    """Reflect colored cells across the row/column marked by color 8.

    The 8-cells identify a horizontal or vertical mirror axis.  Every other
    colored cell is copied to its in-bounds reflected position when that
    position is empty.  Existing cells, including conflicts between colors,
    are preserved.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 8
    ]
    if not markers:
        return out

    marker_rows = {row for row, _ in markers}
    marker_cols = {col for _, col in markers}

    if len(marker_rows) == 1:
        axis = next(iter(marker_rows))
        reflect = lambda row, col: (2 * axis - row, col)
    elif len(marker_cols) == 1:
        axis = next(iter(marker_cols))
        reflect = lambda row, col: (row, 2 * axis - col)
    else:
        # The visible task defines a straight row/column axis.  Leave malformed
        # inputs unchanged rather than guessing an axis.
        return out

    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color in (0, 8):
                continue
            new_row, new_col = reflect(row, col)
            if (
                0 <= new_row < height
                and 0 <= new_col < width
                and grid[new_row][new_col] == 0
            ):
                out[new_row][new_col] = color

    return out
