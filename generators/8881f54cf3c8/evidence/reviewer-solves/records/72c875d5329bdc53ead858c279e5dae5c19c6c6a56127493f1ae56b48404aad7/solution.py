def solve(grid):
    """Apply the Boolean operation encoded by the top-left key."""
    op = int(grid[0][0])

    # The key is metadata for the color-2 object, so exclude (0, 0) from A.
    # For color 3, the visible op-3 example shows that the key itself remains
    # part of B, creating the large normalized span in that demonstration.
    a_raw = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2 and (r, c) != (0, 0)
    }
    b_raw = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    }

    def normalize(cells):
        if not cells:
            return set()
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        return {(r - r0, c - c0) for r, c in cells}

    a = normalize(a_raw)
    b = normalize(b_raw)

    if op == 1:
        result = a | b
    elif op == 2:
        result = a & b
    elif op == 3:
        result = a ^ b
    elif op == 4:
        result = a - b
    else:
        raise ValueError(f"unexpected operation key: {op}")

    all_cells = a | b
    height = max((r for r, _ in all_cells), default=0) + 1
    width = max((c for _, c in all_cells), default=0) + 1
    out = [[0 for _ in range(width)] for _ in range(height)]
    for r, c in result:
        out[r][c] = 4
    return out
