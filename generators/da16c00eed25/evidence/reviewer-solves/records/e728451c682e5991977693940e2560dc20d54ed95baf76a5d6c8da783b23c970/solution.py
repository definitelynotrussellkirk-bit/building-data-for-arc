from collections import Counter


def solve(grid):
    """Complete the missing corner of the axis-aligned rectangle.

    The input contains three cells of one non-background color at three corners
    of a rectangle.  The row and column that occur once identify the missing
    fourth corner.
    """
    out = [row[:] for row in grid]
    colored = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not colored:
        return out

    rows = Counter(r for r, _, _ in colored)
    cols = Counter(c for _, c, _ in colored)
    missing_row = next((r for r, count in rows.items() if count == 1), None)
    missing_col = next((c for c, count in cols.items() if count == 1), None)
    if missing_row is None or missing_col is None:
        return out

    color = Counter(value for _, _, value in colored).most_common(1)[0][0]
    out[missing_row][missing_col] = color
    return out
