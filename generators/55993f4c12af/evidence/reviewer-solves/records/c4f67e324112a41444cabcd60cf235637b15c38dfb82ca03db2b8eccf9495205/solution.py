def solve(grid):
    """Overlay the equal upper and lower panels by nonzero occupancy.

    The input has two equally sized panels stacked vertically.  The output keeps
    their width and one panel's height; a cell is color 4 exactly when either
    aligned input cell is nonzero.
    """
    if not isinstance(grid, list) or not grid or len(grid) % 2:
        raise ValueError("grid must have a positive even number of rows")
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be a nonempty rectangular list of rows")

    half = len(grid) // 2
    return [
        [4 if grid[r][c] != 0 or grid[r + half][c] != 0 else 0 for c in range(width)]
        for r in range(half)
    ]
