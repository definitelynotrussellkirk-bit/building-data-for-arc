"""Visible-example solution for 0c4c1974cbf2."""


def solve(grid):
    height = len(grid)
    width = len(grid[0])
    bars = [
        col
        for col in range(width)
        if all(grid[row][col] == 8 for row in range(height))
    ]
    if len(bars) != 1:
        raise ValueError(f"expected one full-height color-8 divider, got {bars}")
    bar = bars[0]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for col in range(bar):
            reflected = 2 * bar - col
            if (
                grid[row][col] != 0
                and 0 <= reflected < width
                and grid[row][reflected] != 0
            ):
                output[row][reflected] = 2
    return output
