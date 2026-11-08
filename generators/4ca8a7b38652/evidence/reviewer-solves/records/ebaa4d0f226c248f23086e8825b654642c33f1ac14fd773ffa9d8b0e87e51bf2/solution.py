def solve(grid):
    """Upscale each cell by the number of distinct nonzero colors."""
    colors = {value for row in grid for value in row if value != 0}
    factor = len(colors)
    if factor <= 1:
        return [row[:] for row in grid]
    output = []
    for row in grid:
        expanded = [value for value in row for _ in range(factor)]
        output.extend(expanded[:] for _ in range(factor))
    return output
