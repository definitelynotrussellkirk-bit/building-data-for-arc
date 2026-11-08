def solve(grid):
    """Cap maximal horizontal runs of exactly three gray (4) cells with 6s."""
    result = [row[:] for row in grid]

    for r, row in enumerate(grid):
        width = len(row)
        c = 0
        while c < width:
            if row[c] != 4:
                c += 1
                continue

            start = c
            while c < width and row[c] == 4:
                c += 1

            if c - start != 3:
                continue

            if start > 0 and row[start - 1] == 0:
                result[r][start - 1] = 6
            if c < width and row[c] == 0:
                result[r][c] = 6

    return result
