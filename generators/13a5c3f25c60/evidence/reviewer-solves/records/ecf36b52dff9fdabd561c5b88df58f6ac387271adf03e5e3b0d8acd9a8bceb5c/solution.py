from copy import deepcopy


def solve(grid):
    """Use the corner legend: recolor source cells, preserving both legend cells."""
    if not grid or not grid[0]:
        return deepcopy(grid)
    out = deepcopy(grid)
    source = grid[0][0]
    target = grid[0][-1]
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == source and (r, c) not in {(0, 0), (0, width - 1)}:
                out[r][c] = target
    return out
