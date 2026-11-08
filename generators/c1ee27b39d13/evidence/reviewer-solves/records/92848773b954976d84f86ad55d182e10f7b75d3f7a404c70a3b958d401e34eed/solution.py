def solve(grid):
    """Extract cells at intersections of row markers 5 and column markers 4."""
    if not grid or not grid[0]:
        return []

    marked_columns = [
        column
        for column, value in enumerate(grid[0])
        if column > 0 and value == 4
    ]
    marked_rows = [
        row
        for row in range(1, len(grid))
        if grid[row] and grid[row][0] == 5
    ]
    return [[grid[row][column] for column in marked_columns] for row in marked_rows]
