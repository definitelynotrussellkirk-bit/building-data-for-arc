def solve(grid):
    """Keep the two ends of every vertical same-colour run.

    Background cells are 0. A one-cell run is both its own top and bottom,
    so it is retained once.
    """
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [[0 for _ in range(width)] for _ in range(height)]

    for col in range(width):
        row = 0
        while row < height:
            colour = grid[row][col]
            if colour == 0:
                row += 1
                continue

            start = row
            row += 1
            while row < height and grid[row][col] == colour:
                row += 1
            end = row - 1

            out[start][col] = colour
            out[end][col] = colour

    return out
