"""Generator for 7039b2d7.

Rule: uniform divider rows/cols define grid; output is cell-count
rectangle in other color.

Combinatorial axes (8): row_bands, col_bands, palette_kind, band_h_max,
band_w_max, anchor_corner, asymmetry_force, palette_size.
Degenerates: no_dividers, all_dividers, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "eb3171637821"
VERSION = "2.2.0"  # widen band counts 2-8 (output up to 8x8, max dim was 6) + bigger bands, with grid-size clamp <=30; output is intrinsically a monochrome NxM rectangle (dup-outputs is the small output alphabet)
TASK_ID = "eb3171637821"
SUMMARY = (
    "Grid with EXACTLY 2 "
    "COLORS: a CELL_COLOR "
    "(non-0) filling the bg "
    "of all cell bands and "
    "a DIV_COLOR (non-0, "
    "distinct from cell_"
    "color) forming N-1 "
    "FULL DIVIDER ROWS and "
    "M-1 FULL DIVIDER COLUMNS"
    " interleaved with N "
    "row_bands and M col_"
    "bands. Each cell band "
    "has height/width 1-3. "
    "row_bands × col_bands "
    "= 2-4 each. Output "
    "uniq_out=34 (intrinsic "
    "— output is N×M grid "
    "of cell_color only). "
    "Rule (COUNT CELL BANDS, "
    "EMIT N×M FRESH GRID OF "
    "CELL_COLOR): identify "
    "the DIV_COLOR (the "
    "color forming full "
    "rows/cols). COUNT "
    "N_rows = number of "
    "row bands (non-divider "
    "row stripes) and "
    "N_cols = number of "
    "col bands. EMIT a "
    "FRESH (N_rows × "
    "N_cols) OUTPUT GRID "
    "entirely filled with "
    "CELL_COLOR. Net: input "
    "grid → small output "
    "sized by cell-band "
    "count, monochrome cell "
    "color."
)

# Rivals: 'output is input' refuted by demos (output is small N×N).
# 'output is the divider color' refuted by demos showing cell color.
# 'output is the input crop of one cell-band' refuted by demos showing
# N×N where N is the count of bands. 'count divider lines, not bands'
# refuted by demos where N_bands = N_dividers + 1. 'output is 1×1'
# refuted by demos with N_bands ≥ 2. 3 demos with varied row/col band
# counts pin the rule.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "input uses exactly 2 colors: 1 divider color (forms full rows + full cols) + 1 cell color",
    "≥1 full divider row AND ≥1 full divider col (so both row and col bands are countable)",
    "non-divider bands have positive height and width",
    "≥2 row bands AND ≥2 col bands so output dimensions are non-trivial",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_dividers", "all_dividers", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "row_bands":      {"type": "int", "default": "rng 2..8 by diff", "valid": "2..8"},
    "col_bands":      {"type": "int", "default": "rng 2..8 by diff", "valid": "2..8"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "band_h_max":     {"type": "int", "default": "3", "valid": "1..5"},
    "band_w_max":     {"type": "int", "default": "3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|no_dividers|all_dividers|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        rb_lo, rb_hi = 2, 3
        cb_lo, cb_hi = 2, 3
        bh_max = bw_max = 3
    elif difficulty == "hard":
        rb_lo, rb_hi = 5, 8
        cb_lo, cb_hi = 5, 8
        bh_max = bw_max = 6
    else:
        rb_lo, rb_hi = 3, 5
        cb_lo, cb_hi = 3, 5
        bh_max = bw_max = 4
    row_bands = ctx.draw_int("row_bands", rb_lo, rb_hi)
    col_bands = ctx.draw_int("col_bands", cb_lo, cb_hi)
    div_color, cell_color = ctx.draw_distinct_colors("colors", n=2, exclude={0})
    bh_max = int(overrides.get("band_h_max", bh_max))
    bw_max = int(overrides.get("band_w_max", bw_max))
    # clamp per-band width so total grid (bands + dividers) stays <= 30
    bh_cap = max(1, min(bh_max, (30 - (row_bands - 1)) // row_bands))
    bw_cap = max(1, min(bw_max, (30 - (col_bands - 1)) // col_bands))
    band_h = [rng.randint(1, bh_cap) for _ in range(row_bands)]
    band_w = [rng.randint(1, bw_cap) for _ in range(col_bands)]
    h = sum(band_h) + row_bands - 1
    w = sum(band_w) + col_bands - 1
    g = full_grid(h, w, cell_color)
    r = band_h[0]
    for bh in band_h[1:]:
        for c in range(w):
            g[r][c] = div_color
        r += 1 + bh
    c = band_w[0]
    for bw in band_w[1:]:
        for rr in range(h):
            g[rr][c] = div_color
        c += 1 + bw
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Output is, by design, a monochrome N×M cell_color rectangle (band count) —
    a single-color output is correct here, not a no-op. This guards the INPUT:
    exactly 2 colors, with >=1 full divider row AND >=1 full divider col."""
    errs = []
    h = len(grid); w = len(grid[0]) if h else 0
    colors = {v for row in grid for v in row}
    if len(colors) != 2:
        errs.append(f"expected exactly 2 colors, got {sorted(colors)}")
        return errs
    div_rows = [r for r in range(h) if len({grid[r][c] for c in range(w)}) == 1]
    div_cols = [c for c in range(w) if len({grid[r][c] for r in range(h)}) == 1]
    # a divider color forms a full row AND a full col
    div_color = None
    for clr in colors:
        full_r = any(all(grid[r][c] == clr for c in range(w)) for r in range(h))
        full_c = any(all(grid[r][c] == clr for r in range(h)) for c in range(w))
        if full_r and full_c:
            div_color = clr
    if div_color is None:
        errs.append("no divider color forms both a full row and a full col")
        return errs
    has_div_row = any(all(grid[r][c] == div_color for c in range(w)) for r in range(h))
    has_div_col = any(all(grid[r][c] == div_color for r in range(h)) for c in range(w))
    if not (has_div_row and has_div_col):
        errs.append("need >=1 full divider row AND >=1 full divider col")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    if name == "no_dividers":
        return full_grid(h, w, 2)
    if name == "all_dividers":
        return full_grid(h, w, 5)
    if name == "full_grid":
        return full_grid(h, w, 5)
    return full_grid(h, w, 2)
