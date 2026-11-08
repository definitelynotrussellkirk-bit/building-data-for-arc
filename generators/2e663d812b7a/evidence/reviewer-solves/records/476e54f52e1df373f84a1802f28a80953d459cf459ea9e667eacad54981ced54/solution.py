"""Concentric square rings inferred from the visible training examples."""


def solve(grid):
    """Expand the isolated seed using the radius colors in the legend."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height = len(grid)
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("Expected a rectangular grid")

    result = [list(row) for row in grid]
    divider = next(
        row for row in range(1, height)
        if all(color == 5 for color in grid[row])
    )
    legend_row = divider - 1
    palette = list(grid[legend_row])
    seeds = [
        (row, column)
        for row in range(divider + 1, height)
        for column in range(width)
        if grid[row][column] != 0
    ]
    if len(seeds) != 1:
        raise ValueError("Expected one seed below the gray divider")
    seed_row, seed_column = seeds[0]

    # Each legend index is the Chebyshev radius of a square ring.
    for row in range(divider + 1, height):
        for column in range(width):
            radius = max(abs(row - seed_row), abs(column - seed_column))
            result[row][column] = palette[radius] if radius < len(palette) else 0

    # Rings reaching the gray divider mark their nonblack legend entries gray.
    distance_to_divider = seed_row - divider
    for radius, color in enumerate(palette):
        if color != 0 and radius >= distance_to_divider:
            result[legend_row][radius] = 5
    return result
