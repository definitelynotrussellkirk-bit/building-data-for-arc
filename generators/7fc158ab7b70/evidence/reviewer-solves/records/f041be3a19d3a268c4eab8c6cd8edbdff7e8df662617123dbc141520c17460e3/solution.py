def solve(grid):
    """Replace each input cell with a square block sized by nonzero-cell count."""
    if not grid or not grid[0]:
        return []
    scale = sum(value != 0 for row in grid for value in row)
    if scale <= 0:
        return []
    output = []
    for row in grid:
        expanded = [value for value in row for _ in range(scale)]
        output.extend([list(expanded) for _ in range(scale)])
    return output
