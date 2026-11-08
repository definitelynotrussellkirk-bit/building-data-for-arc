def solve(grid):
    """Classify whether the full grid is mirror-symmetric left-to-right."""
    is_vertical_mirror = all(row == row[::-1] for row in grid)
    return [[1 if is_vertical_mirror else 7]]
