def solve(grid):
    """Drop the complete non-background pattern straight down to the bottom edge."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    occupied = [(r, c, value)
                for r, row in enumerate(grid)
                for c, value in enumerate(row)
                if value != 0]
    if not occupied:
        return [list(row) for row in grid]

    bottom = max(r for r, _, _ in occupied)
    shift = height - 1 - bottom
    output = [[0] * width for _ in range(height)]
    for r, c, value in occupied:
        output[r + shift][c] = value
    return output
