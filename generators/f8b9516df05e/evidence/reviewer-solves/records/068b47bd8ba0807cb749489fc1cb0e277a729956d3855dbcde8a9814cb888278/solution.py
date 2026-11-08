def solve(grid):
    """Extend each colored seed rightward through zeros to the next gray 8."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        width = len(row)
        for c, color in enumerate(row):
            if color in (0, 8):
                continue

            # A seed acts only when the next non-background cell to its right
            # is a gray endpoint.  This avoids crossing another colored seed.
            endpoint = c + 1
            while endpoint < width and row[endpoint] == 0:
                endpoint += 1
            if endpoint < width and row[endpoint] == 8:
                for cc in range(c + 1, endpoint):
                    out[r][cc] = color
    return out
