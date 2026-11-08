from copy import deepcopy


def solve(grid):
    """Reflect every non-background cell across the full-height cyan axis."""
    if not grid or not grid[0]:
        return deepcopy(grid)

    height = len(grid)
    width = len(grid[0])
    axis = next(
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    )

    out = deepcopy(grid)
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 0 or col == axis:
                continue
            mirror_col = 2 * axis - col
            if 0 <= mirror_col < width:
                out[row][mirror_col] = value
    return out
