def solve(grid):
    """Cap each horizontal run of at least two 6s with 8 where space exists."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] != 6:
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == 6:
                c += 1
            end = c - 1
            if end - start + 1 < 2:
                continue
            if start > 0 and row[start - 1] == 0:
                out[r][start - 1] = 8
            if end + 1 < len(row) and row[end + 1] == 0:
                out[r][end + 1] = 8
    return out
