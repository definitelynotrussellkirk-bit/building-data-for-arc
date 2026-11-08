from __future__ import annotations

from collections import Counter


def _block_origin(grid, color):
    h, w = len(grid), len(grid[0])
    for r0, c0 in ((0, 0), (0, w - 3), (h - 3, 0), (h - 3, w - 3)):
        if all(grid[r0 + dr][c0 + dc] == color for dr in range(3) for dc in range(3)):
            return r0, c0
    raise ValueError(f"no solid 3x3 corner block for color {color}")


def _inside_block(r, c, origin):
    r0, c0 = origin
    return r0 <= r <= r0 + 2 and c0 <= c <= c0 + 2


def _destination(r, c, origin, h, w):
    r0, c0 = origin
    row_aligned = r0 <= r <= r0 + 2
    col_aligned = c0 <= c <= c0 + 2

    # A left block pulls left; a right block pulls right. Likewise vertically.
    dc = 0 if col_aligned else (-1 if c0 == 0 else 1)
    dr = 0 if row_aligned else (-1 if r0 == 0 else 1)

    rr, cc = r, c
    while True:
        nr, nc = rr + dr, cc + dc
        if not (0 <= nr < h and 0 <= nc < w) or _inside_block(nr, nc, origin):
            return rr, cc
        rr, cc = nr, nc


def solve(grid):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("expected a nonempty rectangular grid")

    h, w = len(grid), len(grid[0])
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    colors = sorted({value for row in grid for value in row if value != background})
    blocks = {color: _block_origin(grid, color) for color in colors}

    moves = []
    for color in colors:
        origin = blocks[color]
        for r in range(h):
            for c in range(w):
                if grid[r][c] == color and not _inside_block(r, c, origin):
                    moves.append((color, (r, c), _destination(r, c, origin, h, w)))

    out = [row[:] for row in grid]
    for _, (r, c), _ in moves:
        out[r][c] = background
    for color, _, (r, c) in moves:
        out[r][c] = color
    return out
