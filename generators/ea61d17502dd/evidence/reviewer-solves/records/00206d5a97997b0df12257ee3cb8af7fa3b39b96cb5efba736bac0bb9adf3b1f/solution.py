from collections import Counter


def solve(grid):
    h, w = len(grid), len(grid[0])

    row_counts = [sum(value > 0 for value in row) for row in grid]
    col_counts = [sum(grid[r][c] > 0 for r in range(h)) for c in range(w)]
    horiz_row = row_counts.index(max(row_counts))
    vert_col = col_counts.index(max(col_counts))

    horiz_vals = [
        grid[horiz_row][c]
        for c in range(w)
        if c != vert_col and grid[horiz_row][c] > 0
    ]
    vert_vals = [
        grid[r][vert_col]
        for r in range(h)
        if r != horiz_row and grid[r][vert_col] > 0
    ]

    def base_and_special(values):
        counts = Counter(values)
        # Counter preserves first-seen order for equal counts, matching the
        # visible examples' natural scan order. Lawful cases have a strict
        # majority, so the tie rule is only defensive.
        base = max(counts, key=counts.get)
        special = next(value for value in values if value != base)
        return base, special

    horiz_base, horiz_spec = base_and_special(horiz_vals)
    vert_base, vert_spec = base_and_special(vert_vals)

    horiz_spec_cols = [
        c for c in range(w)
        if c != vert_col and grid[horiz_row][c] == horiz_spec
    ]
    vert_spec_rows = [
        r for r in range(h)
        if r != horiz_row and grid[r][vert_col] == vert_spec
    ]

    horizontal_primary = grid[horiz_row][vert_col] == horiz_base
    min_row = min([horiz_row, *vert_spec_rows])
    max_row = max([horiz_row, *vert_spec_rows])
    min_col = min(horiz_spec_cols)
    max_col = max(horiz_spec_cols)
    near = min(vert_spec_rows, key=lambda r: abs(r - horiz_row))
    far = max(vert_spec_rows, key=lambda r: abs(r - horiz_row))

    out = [[0] * w for _ in range(h)]
    for r in range(min_row, max_row + 1):
        even_row = (r - min_row) % 2 == 0
        in_vertical_band = min(near, far) <= r <= max(near, far)
        for c in range(min_col, max_col + 1):
            even_col = (c - min_col) % 2 == 0
            if even_row:
                if in_vertical_band:
                    if even_col:
                        value = vert_spec
                    elif r == near and horizontal_primary:
                        value = horiz_base
                    else:
                        value = vert_base
                else:
                    value = horiz_spec if even_col else vert_base
            elif horizontal_primary:
                value = horiz_base
            else:
                value = horiz_base if even_col else vert_base
            out[r][c] = value
    return out
