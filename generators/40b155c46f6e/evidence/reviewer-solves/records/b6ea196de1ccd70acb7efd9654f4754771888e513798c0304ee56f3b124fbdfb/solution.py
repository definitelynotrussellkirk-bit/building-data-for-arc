from collections import Counter


def solve(grid):
    """Make each nonzero horizontal segment its own majority color."""
    out = [list(row) for row in grid]
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] == 0:
                c += 1
                continue
            end = c + 1
            while end < len(row) and row[end] != 0:
                end += 1
            color = Counter(row[c:end]).most_common(1)[0][0]
            out[r][c:end] = [color] * (end - c)
            c = end
    return out
