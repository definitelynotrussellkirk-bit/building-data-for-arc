from copy import deepcopy


def solve(grid):
    """Reflect color-5 cells across the axis selected by the edge marker."""
    height = len(grid)
    width = len(grid[0])
    output = deepcopy(grid)

    top_markers = [col for col, value in enumerate(grid[0]) if value == 2]
    if top_markers:
        orientation = "vertical"
        axis = top_markers[0]
    else:
        orientation = "horizontal"
        axis = next(row for row in range(height) if grid[row][0] == 2)

    sources = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 5
    ]
    for row, col in sources:
        if orientation == "vertical":
            mirror_row, mirror_col = row, 2 * axis - col
        else:
            mirror_row, mirror_col = 2 * axis - row, col
        if 0 <= mirror_row < height and 0 <= mirror_col < width:
            if output[mirror_row][mirror_col] == 0:
                output[mirror_row][mirror_col] = 7
    return output
