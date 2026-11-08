def solve(grid):
    """Fill zeroes immediately between vertical orange (7) endpoints."""
    values = [list(row) for row in grid]
    if not values:
        return []
    out = [row[:] for row in values]
    height = len(values)
    width = len(values[0])
    for row in range(1, height - 1):
        for col in range(width):
            if (
                values[row][col] == 0
                and values[row - 1][col] == 7
                and values[row + 1][col] == 7
            ):
                out[row][col] = 4
    return out
