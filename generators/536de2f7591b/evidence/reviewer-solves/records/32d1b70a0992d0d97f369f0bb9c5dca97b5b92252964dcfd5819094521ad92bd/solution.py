def solve(grid):
    """Slide each contiguous 3-block left to just after its nearest left-hand 8."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        green = [c for c, value in enumerate(row) if value == 3]
        if not green:
            continue
        start, end = green[0], green[-1]
        length = end - start + 1
        left_walls = [c for c in range(start) if row[c] == 8]
        destination = (max(left_walls) + 1) if left_walls else 0

        for c in range(start, end + 1):
            out[r][c] = 0
        for c in range(destination, destination + length):
            out[r][c] = 3
    return out
