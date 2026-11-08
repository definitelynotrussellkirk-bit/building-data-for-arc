def solve(grid):
    """Fill the interiors of every axis-aligned rectangle whose corners are 4."""
    out = [row[:] for row in grid]
    rows_with_fours = {
        r: {c for c, value in enumerate(row) if value == 4}
        for r, row in enumerate(grid)
    }

    height = len(grid)
    for top in range(height):
        for bottom in range(top + 1, height):
            shared_columns = sorted(rows_with_fours[top] & rows_with_fours[bottom])
            for left_index, left in enumerate(shared_columns):
                for right in shared_columns[left_index + 1:]:
                    for r in range(top + 1, bottom):
                        for c in range(left + 1, right):
                            out[r][c] = 2
    return out
