"""
Custom filters, targets, and shape masks — the three composable axes.

Filter: which cells to affect  →  (r, c, v) -> bool
Target: what to do to them     →  (r, c, v) -> new_v  OR  (grid) -> grid
Shape:  where to apply         →  (r, c) -> bool  OR  boolean mask

Composition:
  (apply-filtered grid filter target)
  (apply-in-shape grid shape-mask rule-fn)
  (apply-filtered-in-shape grid filter target shape-mask)

Pre-built filters:
  color-filter, position-filter, neighbor-filter, enclosed-filter, etc.

Pre-built shapes:
  rect-mask, diamond-mask, circle-mask, object-mask, band-mask, etc.
"""

import numpy as np


# ============================================================
# Core composition functions
# ============================================================

def apply_filtered(grid, filter_fn, target_fn):
    """Apply target_fn to cells matching filter_fn.

    filter_fn(r, c, v) -> bool
    target_fn(r, c, v) -> new_value
    """
    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])
    for r in range(h):
        for c in range(w):
            if filter_fn(r, c, g[r][c]):
                g[r][c] = target_fn(r, c, g[r][c])
    return g


def apply_in_shape(grid, shape_mask, rule_fn):
    """Apply rule_fn(grid) but only keep changes within shape_mask.

    shape_mask: 2D boolean array or function(r,c)->bool
    rule_fn: grid -> grid
    """
    g = np.array(grid)
    transformed = np.array(rule_fn([list(row) for row in grid]))

    if callable(shape_mask):
        h, w = g.shape
        for r in range(h):
            for c in range(w):
                if shape_mask(r, c):
                    g[r, c] = transformed[r, c]
    else:
        mask = np.array(shape_mask, dtype=bool)
        g[mask] = transformed[mask]

    return g.tolist()


def apply_filtered_in_shape(grid, filter_fn, target_fn, shape_mask):
    """Apply target to filtered cells, but only within shape.

    The full composition: filter × target × shape.
    """
    g = [list(row) for row in grid]
    h, w = len(g), len(g[0])

    for r in range(h):
        for c in range(w):
            in_shape = shape_mask(r, c) if callable(shape_mask) else shape_mask[r][c]
            if in_shape and filter_fn(r, c, g[r][c]):
                g[r][c] = target_fn(r, c, g[r][c])
    return g


# ============================================================
# Pre-built filters: (r, c, v) -> bool
# ============================================================

def color_filter(color):
    """Match cells of a specific color."""
    return lambda r, c, v: v == color


def not_color_filter(color):
    """Match cells NOT of a specific color."""
    return lambda r, c, v: v != color


def colors_filter(colors):
    """Match cells of any of the given colors."""
    s = set(colors)
    return lambda r, c, v: v in s


def position_filter(r1, c1, r2, c2):
    """Match cells within a rectangle."""
    return lambda r, c, v: r1 <= r <= r2 and c1 <= c <= c2


def row_filter(row):
    """Match cells in a specific row."""
    return lambda r, c, v: r == row


def col_filter(col):
    """Match cells in a specific column."""
    return lambda r, c, v: c == col


def border_filter(h, w):
    """Match cells on the grid border."""
    return lambda r, c, v: r == 0 or r == h-1 or c == 0 or c == w-1


def nonzero_filter(bg=0):
    """Match non-background cells."""
    return lambda r, c, v: v != bg


def combine_filters_and(*filters):
    """All filters must match."""
    return lambda r, c, v: all(f(r, c, v) for f in filters)


def combine_filters_or(*filters):
    """Any filter must match."""
    return lambda r, c, v: any(f(r, c, v) for f in filters)


def negate_filter(f):
    """Invert a filter."""
    return lambda r, c, v: not f(r, c, v)


# ============================================================
# Pre-built targets: (r, c, v) -> new_value
# ============================================================

def const_target(new_color):
    """Always return the same color."""
    return lambda r, c, v: new_color


def map_target(mapping):
    """Apply a color mapping dict."""
    return lambda r, c, v: mapping.get(v, v)


def identity_target():
    """Keep original value."""
    return lambda r, c, v: v


# ============================================================
# Pre-built shape masks: (r, c) -> bool  OR  2D array
# ============================================================

def rect_mask(r1, c1, r2, c2):
    """Rectangular region."""
    return lambda r, c: r1 <= r <= r2 and c1 <= c <= c2


def diamond_mask(center_r, center_c, radius):
    """Diamond/Manhattan-distance mask."""
    return lambda r, c: abs(r - center_r) + abs(c - center_c) <= radius


def circle_mask(center_r, center_c, radius):
    """Circular/Euclidean-distance mask."""
    return lambda r, c: (r - center_r)**2 + (c - center_c)**2 <= radius**2


def chebyshev_mask(center_r, center_c, radius):
    """Square/Chebyshev-distance mask."""
    return lambda r, c: max(abs(r - center_r), abs(c - center_c)) <= radius


def cross_mask(center_r, center_c, h, w):
    """Cross: same row or same column as center."""
    return lambda r, c: r == center_r or c == center_c


def ring_mask(center_r, center_c, inner_r, outer_r):
    """Ring between two Manhattan radii."""
    return lambda r, c: inner_r <= abs(r - center_r) + abs(c - center_c) <= outer_r


def band_row_mask(row_ranges):
    """Match rows within any of the given ranges."""
    def check(r, c):
        return any(r1 <= r <= r2 for r1, r2 in row_ranges)
    return check


def band_col_mask(col_ranges):
    """Match cols within any of the given ranges."""
    def check(r, c):
        return any(c1 <= c <= c2 for c1, c2 in col_ranges)
    return check


def invert_mask(mask_fn):
    """Invert a mask function."""
    return lambda r, c: not mask_fn(r, c)


def union_masks(*masks):
    """Union of multiple masks."""
    return lambda r, c: any(m(r, c) for m in masks)


def intersect_masks(*masks):
    """Intersection of multiple masks."""
    return lambda r, c: all(m(r, c) for m in masks)


def object_mask(obj):
    """Mask matching an object's cells."""
    cells = set(tuple(c) for c in obj["cells"])
    return lambda r, c: (r, c) in cells


def interior_mask(obj, border_width=1):
    """Mask of an object's interior (eroded by border_width cells).
    Rectangular objects: shrink bbox by border_width.
    Non-rectangular: erode the cell set.
    """
    r1, c1, r2, c2 = obj["bbox"]
    cells = set(tuple(c) for c in obj["cells"])
    ir1, ic1 = r1 + border_width, c1 + border_width
    ir2, ic2 = r2 - border_width, c2 - border_width
    if ir1 > ir2 or ic1 > ic2:
        return lambda r, c: False
    # For rectangular objects, just use the shrunk bbox
    if obj["size"] == (r2 - r1 + 1) * (c2 - c1 + 1):
        return lambda r, c: ir1 <= r <= ir2 and ic1 <= c <= ic2
    # For non-rectangular: erode by checking all neighbors at border_width
    from .grid_ops import neighbors_4
    eroded = set(cells)
    for _ in range(border_width):
        boundary = set()
        for pr, pc in eroded:
            # If any neighbor is NOT in the set, this cell is on the boundary
            is_boundary = False
            for nr, nc in [(pr-1,pc),(pr+1,pc),(pr,pc-1),(pr,pc+1)]:
                if (nr, nc) not in eroded:
                    is_boundary = True
                    break
            if is_boundary:
                boundary.add((pr, pc))
        eroded -= boundary
    return lambda r, c: (r, c) in eroded


def border_of_object_mask(obj, border_width=1):
    """Mask of an object's border (the outermost N cells)."""
    int_mask = interior_mask(obj, border_width)
    cells = set(tuple(c) for c in obj["cells"])
    return lambda r, c: (r, c) in cells and not int_mask(r, c)


def expand_mask(mask_fn, h, w, amount=1):
    """Dilate a functional mask by `amount` cells."""
    # Precompute the mask array
    arr = np.array([[mask_fn(r, c) for c in range(w)] for r in range(h)])
    from .grid_ops import dilate_mask
    expanded = dilate_mask(arr, amount)
    return lambda r, c: bool(expanded[r, c])


# ============================================================
# Band-aware masks (for the diamond-projection pattern)
# ============================================================

def band_diamond_mask(grid, ref_r1, ref_c1, ref_r2, ref_c2, bg=0):
    """Diamond mask that expands through band separators.

    Pixels within the reference rect → always True.
    Pixels in same row-band or col-band as ref → always True.
    Other pixels: True if their pixel distance from ref ≤ 2*(band_distance - 1)
    in the perpendicular axis.
    """
    g = np.array(grid)
    h, w = g.shape

    # Internal separators only
    sep_rows = sorted([r for r in range(1, h-1) if np.all(g[r,:] == bg)])
    sep_cols = sorted([c for c in range(1, w-1) if np.all(g[:,c] == bg)])
    has_rsep = len(sep_rows) > 0
    has_csep = len(sep_cols) > 0

    def count_seps(pos, bmin, bmax, seps):
        lo, hi = min(pos, bmin), max(pos, bmax)
        return sum(1 for s in seps if lo < s < hi)

    def check(r, c):
        d_pr = max(0, ref_r1 - r, r - ref_r2)
        d_pc = max(0, ref_c1 - c, c - ref_c2)

        if d_pr == 0 or d_pc == 0:
            return True

        d_rb = count_seps(r, ref_r1, ref_r2, sep_rows) if has_rsep else 0
        d_cb = count_seps(c, ref_c1, ref_c2, sep_cols) if has_csep else 0

        if has_rsep and has_csep:
            return d_pc <= 2 * max(0, d_rb - 1) and d_pr <= 2 * max(0, d_cb - 1)
        elif has_rsep:
            return d_pc <= 2 * max(0, d_rb - 1)
        elif has_csep:
            return d_pr <= 2 * max(0, d_cb - 1)
        return True

    return check
