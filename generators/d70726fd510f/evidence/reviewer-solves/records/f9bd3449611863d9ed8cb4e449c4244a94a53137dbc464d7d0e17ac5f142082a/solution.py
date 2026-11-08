def solve(grid):
    """Compare aligned zero/nonzero occupancy on either side of the divider."""
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) and row for row in grid):
        raise ValueError("Expected a nonempty grid")
    width = len(grid[0])
    if width < 3 or width % 2 != 1 or any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangle with two equal panels and a divider")
    middle = width // 2
    if any(row[middle] != 4 for row in grid):
        raise ValueError("Expected the full central color-4 divider seen in the examples")
    return [[2 if ((row[c] != 0) != (row[middle + 1 + c] != 0)) else 0
             for c in range(middle)] for row in grid]
