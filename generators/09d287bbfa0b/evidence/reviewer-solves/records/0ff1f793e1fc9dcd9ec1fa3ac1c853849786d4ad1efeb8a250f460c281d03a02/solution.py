from collections import Counter


def solve(grid):
    """Reflect every off-cross mark across the two divider lines.

    The most common color is the background.  A different color forms a long
    horizontal/vertical cross.  Cells on that cross stay fixed; every other
    non-background cell is copied to all in-bounds mirror positions across the
    cross.  Mirrors are written from a snapshot in row-major order, which also
    handles the visible example where two opposite marks exchange colors.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    colors = [color for color in counts if color != background]
    if not colors:
        return [row[:] for row in grid]

    # Find the non-background color with the strongest same-color row/column
    # cross.  Using the combined support tolerates an object interrupting one
    # arm of the divider, as occurs in a visible example.
    best = None
    for color in colors:
        row_counts = [sum(value == color for value in row) for row in grid]
        col_counts = [sum(grid[r][c] == color for r in range(height))
                      for c in range(width)]
        axis_row = max(range(height), key=row_counts.__getitem__)
        axis_col = max(range(width), key=col_counts.__getitem__)
        score = row_counts[axis_row] + col_counts[axis_col]
        candidate = (score, row_counts[axis_row], col_counts[axis_col],
                     -axis_row, -axis_col, color, axis_row, axis_col)
        if best is None or candidate > best:
            best = candidate

    _, _, _, _, _, _, axis_row, axis_col = best
    source = [row[:] for row in grid]
    result = [row[:] for row in grid]

    for r in range(height):
        for c in range(width):
            value = source[r][c]
            if value == background or r == axis_row or c == axis_col:
                continue

            reflected_row = 2 * axis_row - r
            reflected_col = 2 * axis_col - c
            targets = (
                (reflected_row, c),
                (r, reflected_col),
                (reflected_row, reflected_col),
            )
            for rr, cc in targets:
                if (0 <= rr < height and 0 <= cc < width
                        and rr != axis_row and cc != axis_col):
                    result[rr][cc] = value

    return result
