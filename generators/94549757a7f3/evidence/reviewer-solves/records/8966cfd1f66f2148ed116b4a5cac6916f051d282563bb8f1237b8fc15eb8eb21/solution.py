def solve(grid):
    """Append red (2) to every right-extendable horizontal green (3) segment."""
    out = [row[:] for row in grid]
    if not grid:
        return out

    width = len(grid[0])
    for r, row in enumerate(grid):
        c = 0
        while c < width:
            if row[c] != 3:
                c += 1
                continue

            start = c
            while c < width and row[c] == 3:
                c += 1

            run_length = c - start
            if run_length >= 2 and c < width and row[c] == 0:
                out[r][c] = 2

    return out
