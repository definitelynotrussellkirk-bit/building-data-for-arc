from copy import deepcopy


def solve(grid):
    """Highlight endpoints of maximal same-color vertical runs of length 3."""
    out = deepcopy(grid)
    height = len(grid)
    width = len(grid[0]) if height else 0
    for col in range(width):
        row = 0
        while row < height:
            color = grid[row][col]
            if color == 0:
                row += 1
                continue
            start = row
            while row < height and grid[row][col] == color:
                row += 1
            if row - start == 3:
                out[start][col] = 8
                out[row - 1][col] = 8
    return out
