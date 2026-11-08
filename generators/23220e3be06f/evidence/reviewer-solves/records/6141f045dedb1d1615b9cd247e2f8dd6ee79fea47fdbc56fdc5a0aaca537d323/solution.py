def solve(grid):
    """Crop the lower object, then flip it according to the corner marker."""
    marker = grid[0][0]

    # The corner cell is an instruction marker, not part of the payload object.
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not cells:
        return []

    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]

    if marker == 5:
        return [row[::-1] for row in crop]
    if marker == 6:
        return crop[::-1]
    return crop
