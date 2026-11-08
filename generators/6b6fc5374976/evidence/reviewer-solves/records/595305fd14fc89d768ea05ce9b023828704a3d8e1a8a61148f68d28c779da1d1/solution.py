def _rotate(mask, turns_cw):
    out = [row[:] for row in mask]
    for _ in range(turns_cw % 4):
        out = [list(row) for row in zip(*out[::-1])]
    return out


def solve(grid):
    h, w = len(grid), len(grid[0])

    ones = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1]
    r0 = min(r for r, _ in ones)
    r1 = max(r for r, _ in ones)
    c0 = min(c for _, c in ones)
    c1 = max(c for _, c in ones)
    motif = [
        [grid[r][c] == 1 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]

    instruction_colors = {
        v
        for row in grid
        for v in row
        if v not in (0, 1, 5, 7, 8)
    }
    instruction = next(iter(instruction_colors))
    turns_by_color = {2: 0, 3: 1, 4: 2, 6: 3}
    motif = _rotate(motif, turns_by_color[instruction])

    p8 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8)
    p7 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7)
    dr, dc = p8[0] - p7[0], p8[1] - p7[1]
    blockers = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5}

    out = [[0] * w for _ in range(h)]
    anchor_r, anchor_c = p8
    motif_cells = [
        (r, c)
        for r, row in enumerate(motif)
        for c, filled in enumerate(row)
        if filled
    ]

    while True:
        cells = [(anchor_r + r, anchor_c + c) for r, c in motif_cells]
        if any(not (0 <= r < h and 0 <= c < w) for r, c in cells):
            break
        if any((r, c) in blockers for r, c in cells):
            break
        for r, c in cells:
            out[r][c] = 9
        anchor_r += dr
        anchor_c += dc

    return out
