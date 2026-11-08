from copy import deepcopy


def solve(grid):
    """Swap which of the two crossing full-span bars owns the overlap."""
    height, width = len(grid), len(grid[0])
    horizontal_rows = [
        row for row in range(height)
        if all(grid[row][column] != 0 for column in range(width))
    ]
    vertical_columns = [
        column for column in range(width)
        if all(grid[row][column] != 0 for row in range(height))
    ]
    if not horizontal_rows or not vertical_columns:
        raise ValueError("expected one full-width bar crossing one full-height bar")

    horizontal_set = set(horizontal_rows)
    vertical_set = set(vertical_columns)
    horizontal_colors = {
        grid[row][column]
        for row in horizontal_rows
        for column in range(width)
        if column not in vertical_set
    }
    vertical_colors = {
        grid[row][column]
        for column in vertical_columns
        for row in range(height)
        if row not in horizontal_set
    }
    overlap_colors = {
        grid[row][column]
        for row in horizontal_rows
        for column in vertical_columns
    }
    if not (
        len(horizontal_colors) == len(vertical_colors) == len(overlap_colors) == 1
    ):
        raise ValueError("bar flanks and overlap must each have one color")

    horizontal_color = next(iter(horizontal_colors))
    vertical_color = next(iter(vertical_colors))
    overlap_color = next(iter(overlap_colors))
    if overlap_color == horizontal_color:
        replacement = vertical_color
    elif overlap_color == vertical_color:
        replacement = horizontal_color
    else:
        raise ValueError("overlap must belong to one of the two bars")

    output = deepcopy(grid)
    for row in horizontal_rows:
        for column in vertical_columns:
            output[row][column] = replacement
    return output
