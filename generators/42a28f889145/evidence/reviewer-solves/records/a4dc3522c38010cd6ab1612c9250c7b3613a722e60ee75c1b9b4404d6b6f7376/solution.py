def solve(grid):
    """Exchange the two nonzero colors while leaving every cell in place."""
    colors = sorted({value for row in grid for value in row if value != 0})
    if len(colors) != 2:
        raise ValueError(f"expected exactly two nonzero colors, found {colors}")
    first, second = colors
    return [
        [second if value == first else first if value == second else value for value in row]
        for row in grid
    ]
