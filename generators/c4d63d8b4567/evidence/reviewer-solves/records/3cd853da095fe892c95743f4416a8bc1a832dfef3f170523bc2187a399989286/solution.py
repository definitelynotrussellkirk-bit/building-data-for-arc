from collections import defaultdict


def solve(grid):
    """Join same-coloured markers that share an unobstructed row or column."""
    original = [row[:] for row in grid]
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0]) if height else 0

    positions = defaultdict(list)
    for r, row in enumerate(original):
        for c, value in enumerate(row):
            if value != 0:
                positions[value].append((r, c))

    for colour, cells in positions.items():
        by_row = defaultdict(list)
        by_col = defaultdict(list)
        for r, c in cells:
            by_row[r].append(c)
            by_col[c].append(r)

        # Use only the original marker positions when selecting endpoints.  A
        # different-coloured cell anywhere inside the interval blocks the line.
        for r, cols in by_row.items():
            cols.sort()
            for left, right in zip(cols, cols[1:]):
                if all(original[r][c] in (0, colour) for c in range(left, right + 1)):
                    for c in range(left, right + 1):
                        if out[r][c] == 0:
                            out[r][c] = colour

        for c, rows in by_col.items():
            rows.sort()
            for top, bottom in zip(rows, rows[1:]):
                if all(original[r][c] in (0, colour) for r in range(top, bottom + 1)):
                    for r in range(top, bottom + 1):
                        if out[r][c] == 0:
                            out[r][c] = colour

    return out
