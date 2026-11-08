def solve(grid):
    """Join consecutive original cyan anchors along rows and columns."""
    result = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    # Read anchor positions only from the original grid.  Painting into result
    # must not create new anchors that trigger secondary bridges.
    for row in range(height):
        columns = [col for col in range(width) if grid[row][col] == 8]
        for left, right in zip(columns, columns[1:]):
            for col in range(left, right + 1):
                result[row][col] = 8

    for col in range(width):
        rows = [row for row in range(height) if grid[row][col] == 8]
        for top, bottom in zip(rows, rows[1:]):
            for row in range(top, bottom + 1):
                result[row][col] = 8

    return result
