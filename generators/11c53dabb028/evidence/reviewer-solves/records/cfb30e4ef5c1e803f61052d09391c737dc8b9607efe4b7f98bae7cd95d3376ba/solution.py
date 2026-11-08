def solve(grid):
    """Invert occupancy using the first nonzero color, then repeat 2 by 2."""
    color = next((cell for row in grid for cell in row if cell != 0), 0)
    tile = [[color if cell == 0 else 0 for cell in row] for row in grid]
    doubled_rows = [row + row for row in tile]
    return doubled_rows + [row[:] for row in doubled_rows]
