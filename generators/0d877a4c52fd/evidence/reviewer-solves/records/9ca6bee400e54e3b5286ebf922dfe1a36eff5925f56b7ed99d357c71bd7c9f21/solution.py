def solve(grid):
    """Complete the missing corner of each color's axis-aligned rectangle."""
    out = [row[:] for row in grid]

    colors = {value for row in grid for value in row if value != 0}
    for color in colors:
        points = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == color
        }
        rows = {r for r, _ in points}
        cols = {c for _, c in points}

        # The examples encode each object as three of the four corners of a
        # non-degenerate, axis-aligned rectangle.
        if len(points) == 3 and len(rows) == 2 and len(cols) == 2:
            missing = {(r, c) for r in rows for c in cols} - points
            if len(missing) == 1:
                r, c = missing.pop()
                out[r][c] = color

    return out
