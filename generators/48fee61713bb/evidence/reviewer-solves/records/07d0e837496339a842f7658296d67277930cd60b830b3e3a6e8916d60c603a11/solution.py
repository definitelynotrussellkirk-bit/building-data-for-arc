def solve(grid):
    """Decode the 3x3-cell picture, apply indicated gravity, and crop."""
    if not grid or not grid[0]:
        return []

    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        raise ValueError("ragged grid")

    # The color-1 line marks an outside edge. The movement direction is the
    # clockwise tangent to that edge: top->right->down->left->up.
    sides = []
    if all(v == 1 for v in grid[0]):
        sides.append("top")
    if all(v == 1 for v in grid[-1]):
        sides.append("bottom")
    if all(row[0] == 1 for row in grid):
        sides.append("left")
    if all(row[-1] == 1 for row in grid):
        sides.append("right")
    if len(sides) != 1:
        raise ValueError(f"expected one color-1 border, found {sides}")
    side = sides[0]

    if side == "top":
        picture = grid[1:]
    elif side == "bottom":
        picture = grid[:-1]
    elif side == "left":
        picture = [row[1:] for row in grid]
    else:  # right
        picture = [row[:-1] for row in grid]

    # After removing the marker border, each logical cell occupies a 3x3
    # window beginning at 1+4*k. Empty windows are logical zeroes.
    logical = []
    for br in range(7):
        out_row = []
        r0 = 1 + 4 * br
        for bc in range(7):
            c0 = 1 + 4 * bc
            colors = {
                picture[r][c]
                for r in range(r0, r0 + 3)
                for c in range(c0, c0 + 3)
                if picture[r][c] not in (0, 1)
            }
            if len(colors) > 1:
                raise ValueError("mixed colors in one logical cell")
            out_row.append(next(iter(colors), 0))
        logical.append(out_row)

    def pack(values, toward_end):
        occupied = [v for v in values if v != 0]
        padding = [0] * (len(values) - len(occupied))
        return padding + occupied if toward_end else occupied + padding

    if side in ("top", "bottom"):
        # top marker -> right; bottom marker -> left
        moved = [pack(row, toward_end=(side == "top")) for row in logical]
    else:
        # left marker -> up; right marker -> down
        columns = list(zip(*logical))
        packed_columns = [
            pack(list(col), toward_end=(side == "right")) for col in columns
        ]
        moved = [list(row) for row in zip(*packed_columns)]

    nonzero_rows = [r for r, row in enumerate(moved) if any(row)]
    nonzero_cols = [
        c for c in range(len(moved[0])) if any(row[c] for row in moved)
    ]
    if not nonzero_rows or not nonzero_cols:
        return []
    r0, r1 = nonzero_rows[0], nonzero_rows[-1]
    c0, c1 = nonzero_cols[0], nonzero_cols[-1]
    return [row[c0 : c1 + 1] for row in moved[r0 : r1 + 1]]
