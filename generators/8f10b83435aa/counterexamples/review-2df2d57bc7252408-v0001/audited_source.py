"""Generator for arc_puzzle_bank_21_set9_s:S9_H7.

Rule: three equal panels separated by 5-bars; cells occupied in at
least two panels merge to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, panel_h, panel_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_dividers, no_overlap_positions, single_panel_active.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f10b83435aa"
VERSION = "2.0.1"
TASK_ID = "8f10b83435aa"
SUMMARY = (
    "Tiled grid: panel_h × W where panel_h ∈ "
    "{6, 7} and W = 14 (three 4-wide panels plus two "
    "divider columns). Layout: (a) THREE "
    "EQUAL PANELS each panel_h rows × 4 "
    "cols arranged left-to-right at column "
    "offsets 0, panel_w+1, 2*(panel_w+1); "
    "(b) TWO FULL-HEIGHT GRAY (color 5) "
    "DIVIDER COLUMNS at cols panel_w and "
    "2*panel_w+1 separating the panels; (c) "
    "6-10 PANEL-LOCAL POSITIONS (rows 0..panel_h-"
    "1 × cols 0..panel_w-1) sampled randomly. "
    "For EACH POSITION i: pick which panels are "
    "ACTIVE — every 4th position is active in "
    "ALL THREE panels, others are active in "
    "exactly 2 random panels. ACTIVE panel "
    "cells at the position are painted with a "
    "canonical color 2. Rule (POSITIONS OCCUPIED IN "
    "AT LEAST TWO PANELS MERGE TO COLOR 8): "
    "OVERLAY the three panels (align by panel-"
    "local position). For EACH panel-local "
    "position (r, c): COUNT how many of the 3 "
    "panels have a non-{0, 5} cell at (r, c). "
    "PRODUCE an OUTPUT — a single panel_h × "
    "panel_w grid: if count ≥ 2, PAINT cell "
    "(r, c) with COLOR 8; else 0. The output "
    "is smaller than input (one panel size). "
    "Net: the majority-occupancy positions "
    "across the three panels appear as cyan-8 "
    "cells in a small output grid."
)

INVARIANTS = [
    "background is 0",
    "two full-height color-5 divider columns split three equal panels",
    "panels share dimensions",
    "some positions are occupied in exactly two or three panels",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_dividers", "no_overlap_positions", "single_panel_active")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "panel_h":        {"type": "int", "default": "rng 5..7", "valid": "4..9"},
    "panel_w":        {"type": "int", "default": "4", "valid": "4"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_positions":    {"type": "int", "default": "rng 6..10", "valid": "1..24"},
    "palette_size":   {"type": "int", "default": "3 incl. {0,2,5}", "valid": "3"},
    "position_bias":  {"type": "str", "default": "three_panels_majority",
                       "valid": "three_panels_majority"},
    "n_distinct_colors": {"type": "int", "default": "3 incl. {0,2,5}", "valid": "3"},
    "density":        {"type": "str", "default": "panels", "valid": "panels"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        ph = ctx.draw_int("panel_h", 6, 6)
        n_lo, n_hi = 5, 6
    elif difficulty == "hard":
        ph = ctx.draw_int("panel_h", 7, 7)
        n_lo, n_hi = 8, 10
    else:
        ph = ctx.draw_int("panel_h", 6, 7)
        n_lo, n_hi = 6, 8
    # Canonical train uses 14-column inputs: 3 panels of width 4 with two
    # full-height color-5 divider columns.  The previous 5..7 panel widths and
    # seven-color foregrounds produced a different task signature.
    pw = 4
    rng = ctx.draw_rng("layout")
    g = full_grid(ph, 3 * pw + 2, 0)
    for r in range(ph):
        g[r][pw] = 5
        g[r][2 * pw + 1] = 5
    n_pos = int(overrides.get("n_positions", ctx.draw_int("n_positions", n_lo, n_hi)))
    positions = rng.sample([(r, c) for r in range(ph) for c in range(pw)], min(n_pos, ph * pw))
    for i, (r, c) in enumerate(positions):
        panels = [0, 1, 2] if i % 4 == 0 else rng.sample([0, 1, 2], 2)
        for panel in panels:
            offset = panel * (pw + 1)
            g[r][offset + c] = 2
    return g


def _draw_from_degenerate(name, rng):
    ph, pw = 5, 5
    g = full_grid(ph, 3 * pw + 2, 0)
    if name == "no_dividers":
        # cells without 5-divider columns → panel boundaries undefined
        for r, c in [(1, 1), (2, 8), (3, 12)]:
            g[r][c] = 4
        return g
    if name == "no_overlap_positions":
        # each position occupied in only one panel → no ≥2-panel merges, output empty
        for r in range(ph):
            g[r][pw] = 5; g[r][2 * pw + 1] = 5
        g[1][1] = 4         # panel 0 only
        g[2][pw + 2] = 6    # panel 1 only
        g[3][2 * pw + 3] = 7 # panel 2 only
        return g
    if name == "single_panel_active":
        # only panel 0 has any cells → no overlap ever, output empty
        for r in range(ph):
            g[r][pw] = 5; g[r][2 * pw + 1] = 5
        for r, c in [(1, 1), (2, 2), (3, 1)]:
            g[r][c] = 4
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """bg=0; exactly two full-height color-5 divider columns split three panels."""
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(div_cols) != 2:
        errs.append(f"expected exactly two full-height color-5 dividers, found {len(div_cols)}")
    elif div_cols != [4, 9] or w != 14:
        errs.append(f"expected canonical 14-wide panel layout with dividers [4, 9], got w={w}, divs={div_cols}")
    bad = sorted({v for row in grid for v in row if v not in {0, 2, 5}})
    if bad:
        errs.append(f"unexpected non-canonical colors outside {{0,2,5}}: {bad}")
    return errs
