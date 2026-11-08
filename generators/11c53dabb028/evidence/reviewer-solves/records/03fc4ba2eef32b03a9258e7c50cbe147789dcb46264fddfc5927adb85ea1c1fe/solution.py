def solve(grid):
    """Invert zero/nonzero occupancy, using the first color, then tile twice."""
    color = next(value for row in grid for value in row if value != 0)
    tile = [[color if value == 0 else 0 for value in row] for row in grid]
    return [row + row for _ in range(2) for row in tile]
