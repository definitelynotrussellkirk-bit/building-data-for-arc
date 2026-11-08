def solve(grid):
    """Complete sparse concentric rectangular frames on the odd-cell lattice."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    # The visible examples use zero spacer rows/columns around an odd-coordinate
    # lattice.  Work on that lattice so each one-cell step is one visible gap.
    rows = list(range(1, height - 1, 2))
    cols = list(range(1, width - 1, 2))
    lattice = [[grid[r][c] for c in cols] for r in rows]
    n_rows = len(rows)
    n_cols = len(cols)

    def first_nonzero(values):
        return next((value for value in values if value != 0), 0)

    for inset in range((min(n_rows, n_cols) + 1) // 2):
        top, bottom = inset, n_rows - 1 - inset
        left, right = inset, n_cols - 1 - inset
        if top > bottom or left > right:
            break

        corners = {
            (top, left),
            (top, right),
            (bottom, left),
            (bottom, right),
        }
        corner_color = first_nonzero(lattice[r][c] for r, c in corners)

        horizontal_cells = [
            lattice[r][c]
            for r in {top, bottom}
            for c in range(left + 1, right)
        ]
        vertical_cells = [
            lattice[r][c]
            for c in {left, right}
            for r in range(top + 1, bottom)
        ]
        horizontal_color = first_nonzero(horizontal_cells)
        vertical_color = first_nonzero(vertical_cells)

        for r, c in corners:
            out[rows[r]][cols[c]] = corner_color
        for c in range(left + 1, right):
            out[rows[top]][cols[c]] = horizontal_color
            out[rows[bottom]][cols[c]] = horizontal_color
        for r in range(top + 1, bottom):
            out[rows[r]][cols[left]] = vertical_color
            out[rows[r]][cols[right]] = vertical_color

    return out
