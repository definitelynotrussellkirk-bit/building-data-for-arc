def solve(grid):
    """Extend each nonzero, non-9 top-row color downward until a 9 blocker."""
    out = [row[:] for row in grid]
    if not out:
        return out

    height = len(out)
    width = len(out[0])
    for col in range(width):
        color = out[0][col]
        if color in (0, 9):
            continue
        for row in range(1, height):
            if out[row][col] == 9:
                break
            if out[row][col] == 0:
                out[row][col] = color
    return out
