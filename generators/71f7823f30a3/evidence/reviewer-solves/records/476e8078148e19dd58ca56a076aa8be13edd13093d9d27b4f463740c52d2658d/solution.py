def solve(grid):
    """Mirror colored cells horizontally around every 9 pivot in their row."""
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]

    for r, row in enumerate(source):
        pivots = [c for c, value in enumerate(row) if value == 9]
        for pivot in pivots:
            for c, value in enumerate(row):
                if value in (0, 9):
                    continue
                mirrored_c = 2 * pivot - c
                if 0 <= mirrored_c < len(row) and result[r][mirrored_c] == 0:
                    result[r][mirrored_c] = value

    return result
