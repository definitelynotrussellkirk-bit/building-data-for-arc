def solve(grid):
    """Fill the room whose number of blue cells matches the corner key."""
    height = len(grid)
    width = len(grid[0])
    key = grid[0][0]

    # The rooms are separated by complete gray (5) rows and columns.  The
    # top-left key may replace the gray cell at (0, 0), so ignore that one
    # position when recognizing the outer separators.
    separator_rows = []
    for r in range(height):
        if all(grid[r][c] == 5 for c in range(width) if not (r == 0 and c == 0)):
            separator_rows.append(r)

    separator_cols = []
    for c in range(width):
        if all(grid[r][c] == 5 for r in range(height) if not (r == 0 and c == 0)):
            separator_cols.append(c)

    target = None
    for top, bottom in zip(separator_rows, separator_rows[1:]):
        for left, right in zip(separator_cols, separator_cols[1:]):
            blue_count = sum(
                grid[r][c] == 2
                for r in range(top + 1, bottom)
                for c in range(left + 1, right)
            )
            if blue_count == key:
                target = (top + 1, bottom, left + 1, right)
                break
        if target is not None:
            break

    # Remove all clues except gray separators.  A gray-valued key is naturally
    # indistinguishable from the border and therefore remains gray, matching
    # the visible examples.
    out = [[5 if grid[r][c] == 5 else 0 for c in range(width)] for r in range(height)]

    if target is not None:
        top, bottom, left, right = target
        for r in range(top, bottom):
            for c in range(left, right):
                out[r][c] = 8

    return out
