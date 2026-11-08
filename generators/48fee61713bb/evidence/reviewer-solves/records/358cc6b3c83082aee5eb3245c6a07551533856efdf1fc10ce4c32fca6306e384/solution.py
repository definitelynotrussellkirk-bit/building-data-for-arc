def solve(grid):
    """Collapse framed 3x3 tiles, then apply the edge-indicated gravity."""
    h, w = len(grid), len(grid[0])

    if all(value == 1 for value in grid[0]):
        side = "top"
    elif all(value == 1 for value in grid[-1]):
        side = "bottom"
    elif all(row[0] == 1 for row in grid):
        side = "left"
    elif all(row[-1] == 1 for row in grid):
        side = "right"
    else:
        raise ValueError("missing direction border")

    row_start = 2 if side == "top" else 1
    col_start = 2 if side == "left" else 1
    row_anchors = list(range(row_start, h - 2, 4))
    col_anchors = list(range(col_start, w - 2, 4))

    # The middle lattice lane is the separator between the two source panels.
    if side in ("left", "right"):
        row_anchors.pop(len(row_anchors) // 2)
    else:
        col_anchors.pop(len(col_anchors) // 2)

    compact = []
    for r in row_anchors:
        row = []
        for c in col_anchors:
            color = grid[r][c]
            row.append(color if color not in (0, 1) else 0)
        compact.append(row)

    if side == "top":       # clockwise along the top edge
        return [[0] * (len(row) - len(nz)) + nz
                for row in compact
                for nz in [[value for value in row if value]]]
    if side == "bottom":    # clockwise along the bottom edge
        return [[value for value in row if value] +
                [0] * (len(row) - sum(value != 0 for value in row))
                for row in compact]

    out = [[0 for _ in compact[0]] for _ in compact]
    for c in range(len(compact[0])):
        values = [compact[r][c] for r in range(len(compact)) if compact[r][c]]
        start = 0 if side == "left" else len(compact) - len(values)
        for offset, value in enumerate(values):
            out[start + offset][c] = value
    return out
