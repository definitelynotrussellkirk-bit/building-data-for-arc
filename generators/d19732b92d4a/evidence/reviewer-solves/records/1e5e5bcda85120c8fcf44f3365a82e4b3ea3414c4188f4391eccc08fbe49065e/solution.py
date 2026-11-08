from copy import deepcopy


def solve(grid):
    """Complete any length-3 monochrome diagonal whose center is blank."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0

    # Read endpoints from the original grid so newly filled centers cannot create
    # additional patterns during the same pass.
    for row in range(height - 2):
        for col in range(width):
            color = grid[row][col]
            if color == 0:
                continue
            for delta_col in (-2, 2):
                end_col = col + delta_col
                mid_col = col + delta_col // 2
                if not (0 <= end_col < width):
                    continue
                if grid[row + 2][end_col] != color:
                    continue
                if grid[row + 1][mid_col] == 0:
                    out[row + 1][mid_col] = color

    return out
