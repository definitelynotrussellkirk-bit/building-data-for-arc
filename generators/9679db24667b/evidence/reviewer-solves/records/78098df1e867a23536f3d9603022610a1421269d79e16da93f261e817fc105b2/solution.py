def solve(grid):
    """Replace 9 in a row only when that row has one other nonzero color."""
    output = [list(row) for row in grid]
    for r, row in enumerate(grid):
        source_colors = set(row) - {0, 9}
        if len(source_colors) == 1:
            replacement = next(iter(source_colors))
            output[r] = [replacement if value == 9 else value for value in row]
    return output
