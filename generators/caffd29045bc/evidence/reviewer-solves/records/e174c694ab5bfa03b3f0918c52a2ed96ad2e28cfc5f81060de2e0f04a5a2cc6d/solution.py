import copy


def solve(grid):
    """Copy each colored non-guide cell across the full color-9 column."""
    if not grid or not grid[0]:
        return copy.deepcopy(grid)
    axes = [
        c for c in range(len(grid[0]))
        if all(row[c] == 9 for row in grid)
    ]
    if len(axes) != 1:
        return copy.deepcopy(grid)
    axis = axes[0]
    out = copy.deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            mirrored = 2 * axis - c
            if value not in (0, 9) and 0 <= mirrored < len(row):
                out[r][mirrored] = value
    return out
