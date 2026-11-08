def solve(grid):
    """Join the unique red (2) cell to the unique green (3) cell with an azure L."""
    out = [row[:] for row in grid]
    red = None
    green = None
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 2:
                red = (r, c)
            elif value == 3:
                green = (r, c)

    if red is None or green is None:
        return out

    red_r, red_c = red
    green_r, green_c = green

    # First travel horizontally from red to green's column.
    dc = 1 if green_c > red_c else -1
    if green_c != red_c:
        c = red_c + dc
        while True:
            if (red_r, c) != green:
                out[red_r][c] = 8
            if c == green_c:
                break
            c += dc

    # Then travel vertically along green's column, excluding the green endpoint.
    if green_r != red_r:
        dr = 1 if green_r > red_r else -1
        r = red_r + dr
        while r != green_r:
            out[r][green_c] = 8
            r += dr

    return out
