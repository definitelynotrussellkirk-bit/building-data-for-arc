"""Helpers for regular tile-lattice generators."""
from __future__ import annotations

Grid = list[list[int]]


def assemble_tiles(tile_matrix: list[list[Grid]], divider_color: int = 9) -> Grid:
    """Assemble equal-sized tiles with one-cell divider rows and columns."""
    rows = len(tile_matrix)
    cols = len(tile_matrix[0])
    tile_h = len(tile_matrix[0][0])
    tile_w = len(tile_matrix[0][0][0])
    out_h = rows * tile_h + rows - 1
    out_w = cols * tile_w + cols - 1
    out = [[divider_color] * out_w for _ in range(out_h)]
    for rr, tile_row in enumerate(tile_matrix):
        for cc, tile in enumerate(tile_row):
            top = rr * (tile_h + 1)
            left = cc * (tile_w + 1)
            for r in range(tile_h):
                for c in range(tile_w):
                    out[top + r][left + c] = tile[r][c]
    return out


def blank_tile(h: int = 3, w: int = 3, color: int = 0) -> Grid:
    """Create a small tile."""
    return [[color] * w for _ in range(h)]
