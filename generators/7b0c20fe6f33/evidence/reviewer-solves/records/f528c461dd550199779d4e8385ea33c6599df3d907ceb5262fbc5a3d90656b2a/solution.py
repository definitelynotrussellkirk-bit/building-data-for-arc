"""Visible-example solution for 7b0c20fe6f33."""


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    height, width = len(grid), len(grid[0])
    blue = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    red = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if len(blue) != 1 or len(red) != 1:
        raise ValueError("expected exactly one blue and one red marker")

    dr = red[0][0] - blue[0][0]
    dc = red[0][1] - blue[0][1]
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in range(height):
        for c in range(width):
            value = grid[r][c]
            source_r, source_c = r - dr, c - dc
            translated_from_green = (
                0 <= source_r < height
                and 0 <= source_c < width
                and grid[source_r][source_c] == 3
            )
            if value in (1, 2):
                output[r][c] = value
            elif translated_from_green:
                output[r][c] = 8
            elif value != 0:
                output[r][c] = value
    return output
