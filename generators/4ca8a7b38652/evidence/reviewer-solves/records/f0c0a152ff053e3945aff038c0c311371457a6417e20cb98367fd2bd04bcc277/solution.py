def solve(grid):
    """Upscale each cell by the number of distinct nonzero input colors."""
    factor = len({value for row in grid for value in row if value != 0})
    return [
        [grid[row // factor][col // factor] for col in range(len(grid[0]) * factor)]
        for row in range(len(grid) * factor)
    ]
