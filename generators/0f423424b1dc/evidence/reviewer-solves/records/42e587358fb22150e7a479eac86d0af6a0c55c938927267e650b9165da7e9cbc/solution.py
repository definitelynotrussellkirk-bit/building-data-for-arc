from collections import defaultdict


def solve(grid):
    """Join unobstructed equal-colour markers that share a column."""
    out = [row[:] for row in grid]
    positions = defaultdict(list)

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions[(value, c)].append(r)

    for (value, c), rows in positions.items():
        if len(rows) < 2:
            continue
        rows.sort()
        for top, bottom in zip(rows, rows[1:]):
            segment = [grid[r][c] for r in range(top, bottom + 1)]
            if all(cell in (0, value) for cell in segment):
                for r in range(top, bottom + 1):
                    out[r][c] = value

    return out
