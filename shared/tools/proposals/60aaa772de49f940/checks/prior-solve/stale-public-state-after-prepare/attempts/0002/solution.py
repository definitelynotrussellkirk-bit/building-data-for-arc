def solve(grid):
    out = [row[:] for row in grid]
    start = next((r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value == 2)
    end = next((r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 3)
    r, c = start
    gr, gc = end
    while c != gc:
        c += 1 if gc > c else -1
        if (r, c) != end:
            out[r][c] = 8
    while r != gr:
        r += 1 if gr > r else -1
        if (r, c) != end:
            out[r][c] = 8
    return out
