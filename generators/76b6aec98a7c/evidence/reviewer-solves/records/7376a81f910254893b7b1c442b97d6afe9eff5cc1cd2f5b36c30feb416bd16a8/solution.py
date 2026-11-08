def _bbox(cells):
    rows, cols = zip(*cells)
    return min(rows), min(cols), max(rows) + 1, max(cols) + 1


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def solve(grid):
    """Expand the external 2..5 code rectangle into rotated motif tiles."""
    h, w = len(grid), len(grid[0])

    frame_cells = [
        (r, c) for r in range(h) for c in range(w) if grid[r][c] == 1
    ]
    r0, c0, r1, c1 = _bbox(frame_cells)
    motif = [list(row[c0 + 1:c1 - 1]) for row in grid[r0 + 1:r1 - 1]]

    frame_rect = {
        (r, c) for r in range(r0, r1) for c in range(c0, c1)
    }
    code_cells = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] in (2, 3, 4, 5) and (r, c) not in frame_rect
    ]
    cr0, cc0, cr1, cc1 = _bbox(code_cells)
    codes = [list(row[cc0:cc1]) for row in grid[cr0:cr1]]

    tile_h, tile_w = len(motif), len(motif[0])
    out = [[0] * (len(codes[0]) * tile_w) for _ in range(len(codes) * tile_h)]
    for br, code_row in enumerate(codes):
        for bc, code in enumerate(code_row):
            tile = [row[:] for row in motif]
            for _ in range(code - 2):
                tile = _rotate_cw(tile)
            for dr, row in enumerate(tile):
                for dc, value in enumerate(row):
                    out[br * tile_h + dr][bc * tile_w + dc] = value
    return out
