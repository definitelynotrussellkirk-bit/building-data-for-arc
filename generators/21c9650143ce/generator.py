"""Generator for arc_puzzle_bank_fifth21:M30 — two-row color legend recolors body.

Rule: rows 0 and 1 define a source-to-target color map. Body cells are
recolored according to that map while the legend rows stay in place.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_legend, no_body_use, body_uses_unknown_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "21c9650143ce"
VERSION = "2.0.1"


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rows 0 and 1 define paired source→target map; body rows have source colors."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h < 3:
        return [f"grid too short: {h} rows (need >=3: 2 legend + >=1 body)"]
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
        return errs
    row0_nz = [c for c in range(w) if grid[0][c] != 0]
    row1_nz = [c for c in range(w) if grid[1][c] != 0]
    if not row0_nz:
        errs.append("row 0 has no source colors for the map")
    if len(row0_nz) != len(row1_nz):
        errs.append(f"row 0/1 non-zero counts differ: {len(row0_nz)} vs {len(row1_nz)}")
    return errs
TASK_ID = "21c9650143ce"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) "
    "structured as: (a) ROW 0 = SOURCE "
    "LEGEND with 2-4 source colors "
    "at sorted random columns; (b) "
    "ROW 1 = TARGET LEGEND with the "
    "matching destination colors at "
    "the same columns; (c) ROWS 2..h-1 "
    "= BODY with ~38% density of "
    "cells in SOURCE colors only "
    "(scattered). At least one body "
    "cell is guaranteed at (2, 0) "
    "in the first source color. "
    "Rule (LEGEND-DIRECTED RECOLOR): "
    "build a MAP {src → dst} from "
    "rows 0 and 1 (for each non-zero "
    "col c, map[row0[c]] = row1[c]). "
    "For EACH BODY CELL (rows 2..h-1) "
    "with a source-color value v, "
    "RECOLOR it to map[v]. Cells in "
    "non-mapped colors or 0 stay. "
    "Net: top-two-row legend "
    "translates body source colors "
    "to their dest colors."
)

INVARIANTS = [
    "row 0 source colors align with row 1 target colors",
    "body cells use only source colors and background",
    "at least one mapped body cell changes color",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_legend", "no_body_use", "body_uses_unknown_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..4", "valid": "2..5"},
    "palette_size":   {"type": "int", "default": "rng 4..8", "valid": "4..9"},
    "position_bias":  {"type": "str", "default": "two_row_legend_with_body",
                       "valid": "two_row_legend_with_body"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..8", "valid": "4..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        n_pairs = min(ctx.draw_int("n_pairs", 2, 2), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n_pairs = min(ctx.draw_int("n_pairs", 3, 4), w)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_pairs = min(ctx.draw_int("n_pairs", 2, 4), w)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_pairs * 2)
    srcs = colors[:n_pairs]
    dsts = colors[n_pairs:]
    g = full_grid(h, w, 0)
    cols = sorted(rng.sample(range(w), n_pairs))
    for c, src, dst in zip(cols, srcs, dsts):
        g[0][c] = src
        g[1][c] = dst
    for r in range(2, h):
        for c in range(w):
            if rng.random() < 0.38:
                g[r][c] = rng.choice(srcs)
    g[2][0] = srcs[0]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "no_legend":
        # body cells but top two rows blank → no recolor mapping
        g[3][3] = 4
        g[5][6] = 6
        return g
    if name == "no_body_use":
        # legend present but body has no source-color cells → rule has nothing
        g[0][0] = 4; g[0][1] = 6
        g[1][0] = 6; g[1][1] = 7
        for r in range(2, h):
            for c in range(w): g[r][c] = 9   # body uses 9 only, none in srcs
        return g
    if name == "body_uses_unknown_colors":
        # body uses colors NOT in the legend → no mapping for those cells
        g[0][0] = 4; g[0][1] = 6
        g[1][0] = 6; g[1][1] = 7
        g[3][3] = 9; g[5][5] = 8   # 9 and 8 not in {4,6}
        return g
    return g
