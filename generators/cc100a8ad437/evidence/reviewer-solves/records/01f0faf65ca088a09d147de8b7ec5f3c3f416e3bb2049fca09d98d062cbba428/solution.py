"""Visible-only solution for the reviewer blind puzzle."""

from collections import Counter


def solve(grid):
    """Find copies of the left-hand stencil in the right-hand field.

    A solid nonzero separator column splits the reference stencil from the
    search field.  Each same-orientation occurrence of the stencil's color is
    replaced by an 8-filled rectangle spanning the stencil's bounding box.
    Other foreground cells are clutter and are not copied to the output.
    """
    if not grid or not grid[0]:
        return []

    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")

    separator_candidates = []
    for col in range(width):
        value = grid[0][col]
        if value != 0 and all(grid[row][col] == value for row in range(height)):
            separator_candidates.append(col)
    if not separator_candidates:
        raise ValueError("no solid nonzero separator column found")

    separator = separator_candidates[0]
    left_colors = Counter(
        grid[row][col]
        for row in range(height)
        for col in range(separator)
        if grid[row][col] != 0
    )
    if not left_colors:
        raise ValueError("no reference stencil found left of separator")
    stencil_color = left_colors.most_common(1)[0][0]

    points = [
        (row, col)
        for row in range(height)
        for col in range(separator)
        if grid[row][col] == stencil_color
    ]
    min_row = min(row for row, _ in points)
    max_row = max(row for row, _ in points)
    min_col = min(col for _, col in points)
    max_col = max(col for _, col in points)
    stencil = {(row - min_row, col - min_col) for row, col in points}
    stencil_height = max_row - min_row + 1
    stencil_width = max_col - min_col + 1

    field_start = separator + 1
    output_width = width - field_start
    output = [[0] * output_width for _ in range(height)]

    for top in range(height - stencil_height + 1):
        for left in range(field_start, width - stencil_width + 1):
            if all(
                grid[top + drow][left + dcol] == stencil_color
                for drow, dcol in stencil
            ):
                out_left = left - field_start
                for row in range(top, top + stencil_height):
                    for col in range(out_left, out_left + stencil_width):
                        output[row][col] = 8

    return output
