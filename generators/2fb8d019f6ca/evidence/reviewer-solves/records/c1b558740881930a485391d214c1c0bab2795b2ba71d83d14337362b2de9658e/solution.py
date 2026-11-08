def solve(grid):
    """Copy the upper-left connected shape to each blue anchor."""
    height = len(grid)
    width = len(grid[0])
    anchors = [(r, c) for r, row in enumerate(grid)
               for c, value in enumerate(row) if value == 8]

    shape = set()
    pending = [(0, 0)]
    while pending:
        r, c = pending.pop()
        if not (0 <= r < height and 0 <= c < width):
            continue
        if (r, c) in shape or grid[r][c] in (0, 8):
            continue
        shape.add((r, c))
        pending.extend(((r - 1, c), (r + 1, c),
                        (r, c - 1), (r, c + 1)))

    result = [[0] * width for _ in range(height)]
    for anchor_r, anchor_c in anchors:
        for r, c in shape:
            target_r, target_c = anchor_r + r, anchor_c + c
            if target_r < height and target_c < width:
                result[target_r][target_c] = grid[r][c]
    return result
