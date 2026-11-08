def solve(grid):
    """Extend colored markers relative to the solid gray divider.

    Color 1 extends away from the divider to the outside edge. Color 2
    extends toward the divider, stopping immediately before it. The visible
    examples use a horizontal divider; the vertical case is handled by the
    same inferred rule.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    divider_rows = [r for r, row in enumerate(grid) if all(value == 5 for value in row)]
    divider_cols = [
        c for c in range(width) if all(grid[r][c] == 5 for r in range(height))
    ]

    if len(divider_rows) == 1:
        divider = divider_rows[0]
        for r in range(height):
            if r == divider:
                continue
            for c in range(width):
                color = grid[r][c]
                if color not in (1, 2):
                    continue
                if color == 1:  # away from divider
                    rows = range(0, r + 1) if r < divider else range(r, height)
                else:  # toward divider
                    rows = range(r, divider) if r < divider else range(divider + 1, r + 1)
                for rr in rows:
                    if out[rr][c] == 0:
                        out[rr][c] = color
        return out

    if len(divider_cols) == 1:
        divider = divider_cols[0]
        for r in range(height):
            for c in range(width):
                if c == divider:
                    continue
                color = grid[r][c]
                if color not in (1, 2):
                    continue
                if color == 1:  # away from divider
                    cols = range(0, c + 1) if c < divider else range(c, width)
                else:  # toward divider
                    cols = range(c, divider) if c < divider else range(divider + 1, c + 1)
                for cc in cols:
                    if out[r][cc] == 0:
                        out[r][cc] = color
        return out

    raise ValueError("expected exactly one solid gray divider row or column")
