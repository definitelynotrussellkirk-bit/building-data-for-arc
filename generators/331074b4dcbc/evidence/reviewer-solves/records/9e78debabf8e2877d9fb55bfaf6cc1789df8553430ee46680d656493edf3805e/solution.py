def solve(grid):
    """Tile the leading color key across each gray (8) run below it."""
    out = [row[:] for row in grid]

    key = []
    for value in grid[0]:
        if value == 0:
            break
        key.append(value)
    if not key:
        return out

    # The first row is the legend.  For every target row, restart the key at
    # the left edge of each contiguous gray run.
    for r in range(1, len(grid)):
        c = 0
        while c < len(grid[r]):
            if grid[r][c] != 8:
                c += 1
                continue
            start = c
            while c < len(grid[r]) and grid[r][c] == 8:
                out[r][c] = key[(c - start) % len(key)]
                c += 1
    return out
