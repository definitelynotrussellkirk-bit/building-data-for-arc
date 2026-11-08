"""
Grid algebra — element-wise operations, masks, broadcasting, zipping.

The primitives that let you compose grid operations like matrix math.
"""

import numpy as np


def grid_add(g1, g2, bg=0):
    """Element-wise add: non-bg values from g2 overwrite g1. Like overlay."""
    a1, a2 = np.array(g1), np.array(g2)
    result = a1.copy()
    mask = a2 != bg
    result[mask] = a2[mask]
    return result.tolist()


def grid_subtract(g1, g2, bg=0):
    """Remove from g1 wherever g2 is non-bg. Set those cells to bg."""
    a1, a2 = np.array(g1), np.array(g2)
    result = a1.copy()
    result[a2 != bg] = bg
    return result.tolist()


def grid_intersect(g1, g2, bg=0):
    """Keep only cells where BOTH grids are non-bg. Use g1's values."""
    a1, a2 = np.array(g1), np.array(g2)
    result = np.full_like(a1, bg)
    mask = (a1 != bg) & (a2 != bg)
    result[mask] = a1[mask]
    return result.tolist()


def grid_xor(g1, g2, bg=0):
    """Cells that are non-bg in exactly ONE grid."""
    a1, a2 = np.array(g1), np.array(g2)
    result = np.full_like(a1, bg)
    only1 = (a1 != bg) & (a2 == bg)
    only2 = (a1 == bg) & (a2 != bg)
    result[only1] = a1[only1]
    result[only2] = a2[only2]
    return result.tolist()


def grid_where(grid, pred_fn, bg=0):
    """Boolean mask: 1 where pred_fn(value) is true, 0 elsewhere."""
    g = np.array(grid)
    return [[1 if pred_fn(int(g[r, c])) else 0
             for c in range(g.shape[1])] for r in range(g.shape[0])]


def grid_mask_to_cells(mask):
    """Convert boolean mask grid to list of [r, c] positions."""
    m = np.array(mask)
    return [[int(r), int(c)] for r, c in zip(*np.where(m != 0))]


def cells_to_grid_mask(cells, h, w):
    """Convert cell list to boolean mask grid."""
    mask = [[0] * w for _ in range(h)]
    for cell in cells:
        r, c = cell[0], cell[1]
        if 0 <= r < h and 0 <= c < w:
            mask[r][c] = 1
    return mask


def zip_grids(g1, g2, fn):
    """Combine two grids cell-by-cell: fn(v1, v2) → result."""
    a1, a2 = np.array(g1), np.array(g2)
    h, w = a1.shape
    return [[fn(int(a1[r, c]), int(a2[r, c])) for c in range(w)] for r in range(h)]


def reduce_rows(grid, fn, init=None):
    """Apply fn across each row. fn(accumulator, row_list) → new_acc."""
    result = init
    for row in grid:
        result = fn(result, list(row))
    return result


def reduce_cols(grid, fn, init=None):
    """Apply fn across each column."""
    g = np.array(grid)
    result = init
    for c in range(g.shape[1]):
        col = g[:, c].tolist()
        result = fn(result, col)
    return result


def map_rows(grid, fn):
    """Apply fn to each row. fn(row_list) → new_row_list."""
    return [fn(list(row)) for row in grid]


def map_cols(grid, fn):
    """Apply fn to each column. fn(col_list) → new_col_list."""
    g = np.array(grid)
    h, w = g.shape
    result = g.copy()
    for c in range(w):
        new_col = fn(g[:, c].tolist())
        for r in range(h):
            result[r, c] = new_col[r]
    return result.tolist()


def grid_eq(g1, g2):
    """Boolean mask: 1 where g1 == g2, 0 where different."""
    a1, a2 = np.array(g1), np.array(g2)
    return (a1 == a2).astype(int).tolist()


def grid_diff_mask(g1, g2):
    """Boolean mask: 1 where g1 != g2."""
    a1, a2 = np.array(g1), np.array(g2)
    return (a1 != a2).astype(int).tolist()


def broadcast_shape_to_grid(shape_data, h, w, bg=0):
    """Tile a small shape to fill an h×w grid."""
    s = np.array(shape_data)
    sh, sw = s.shape
    result = np.full((h, w), bg, dtype=int)
    for r in range(h):
        for c in range(w):
            v = s[r % sh, c % sw]
            if v != bg:
                result[r, c] = v
    return result.tolist()
