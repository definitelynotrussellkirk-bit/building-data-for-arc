def solve(grid):
    """Expand every cell to a two-by-two block of its original color."""
    output = []
    for row in grid:
        expanded = [color for color in row for _ in range(2)]
        output.extend([expanded[:], expanded[:]])
    return output
