def solve(grid):
    """Extend the lone foreground cell counterclockwise to its ring corner."""
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    counts = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    background = max(counts, key=counts.get)

    foreground = [
        (r, c, grid[r][c])
        for r in range(height)
        for c in range(width)
        if grid[r][c] != background
    ]
    if len(foreground) != 1:
        return out

    r, c, color = foreground[0]
    distances = (
        (r, "top"),
        (width - 1 - c, "right"),
        (height - 1 - r, "bottom"),
        (c, "left"),
    )
    inset, side = min(distances, key=lambda item: item[0])

    if side == "top":
        for cc in range(inset, c + 1):
            out[r][cc] = color
    elif side == "right":
        for rr in range(inset, r + 1):
            out[rr][c] = color
    elif side == "bottom":
        for cc in range(c, width - inset):
            out[r][cc] = color
    else:  # left
        for rr in range(r, height - inset):
            out[rr][c] = color

    return out
