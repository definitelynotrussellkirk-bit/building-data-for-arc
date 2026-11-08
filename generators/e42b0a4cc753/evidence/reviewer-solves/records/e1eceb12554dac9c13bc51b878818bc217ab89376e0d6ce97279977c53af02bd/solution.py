def solve(grid):
    """Fill background cells from the nearest interior seed by Manhattan distance.

    Equal-distance cells use the first seed in row-major order.  The monochrome
    frame and the original seed cells are preserved.
    """
    result = [row[:] for row in grid]
    if not grid or not grid[0]:
        return result

    frame_color = grid[0][0]
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, frame_color)
    ]
    if not seeds:
        return result

    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0:
                seed_row, seed_col, seed_color = min(
                    seeds,
                    key=lambda seed: abs(row - seed[0]) + abs(col - seed[1]),
                )
                result[row][col] = seed_color
    return result
