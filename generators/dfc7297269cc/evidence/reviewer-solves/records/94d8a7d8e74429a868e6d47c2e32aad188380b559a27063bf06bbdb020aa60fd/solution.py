from copy import deepcopy


def solve(grid):
    """Fill a zero exactly between equal nonzero horizontal neighbours."""
    out = deepcopy(grid)
    for row in range(len(grid)):
        for col in range(1, len(grid[row]) - 1):
            color = grid[row][col - 1]
            if color != 0 and grid[row][col] == 0 and grid[row][col + 1] == color:
                out[row][col] = color
    return out
