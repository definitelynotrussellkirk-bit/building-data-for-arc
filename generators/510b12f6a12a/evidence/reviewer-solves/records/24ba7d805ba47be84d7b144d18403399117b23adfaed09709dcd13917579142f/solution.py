def solve(grid):
    """Paint intersections of unobstructed border-launched rays."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    output = [[0 for _ in range(width)] for _ in range(height)]

    # Every 2 on the top border launches a downward ray.  Every 1 on the
    # left border launches a rightward ray.  A 5 blocks either ray.
    active_vertical = {column for column in range(1, width) if grid[0][column] == 2}
    for row in range(1, height):
        horizontal_active = grid[row][0] == 1
        for column in range(1, width):
            if grid[row][column] == 5:
                active_vertical.discard(column)
                horizontal_active = False
                continue
            if horizontal_active and column in active_vertical:
                output[row][column] = 6

    return output
