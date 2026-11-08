"""A rule inferred solely from the visible blind-solve demonstrations."""


def solve(grid):
    output = [row[:] for row in grid]
    points_by_color = {}
    for row, values in enumerate(grid):
        for column, color in enumerate(values):
            if color != 0:
                points_by_color.setdefault(color, []).append((row, column))

    vertical = []
    horizontal = []
    for color, points in points_by_color.items():
        if len(points) != 2:
            continue
        (r0, c0), (r1, c1) = points
        if c0 == c1:
            vertical.append((color, min(r0, r1), max(r0, r1), c0))
        elif r0 == r1:
            horizontal.append((color, r0, min(c0, c1), max(c0, c1)))

    for color, first_row, last_row, column in vertical:
        for row in range(first_row, last_row + 1):
            output[row][column] = color
    for color, row, first_column, last_column in horizontal:
        for column in range(first_column, last_column + 1):
            output[row][column] = color
    return output
