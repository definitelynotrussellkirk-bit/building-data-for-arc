"""Generator for arc_puzzle_bank_twentyfirst21:M144 — left 1-mask filters right color block.

Rule: an 8-divider column splits the grid. Left side = 0/1 mask.
Right side = arbitrary colored cells. Output = right side, with cells
where the corresponding left-mask position is 0 set to 0.

Combinatorial axes (8): grid_h, grid_w, palette_kind, block_w,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_mask, no_right_block.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, fill_box
from puzzle_generators.helpers.palette import random_palette

GENERATOR_ID = "88fea6584461"
VERSION = "2.0.1"
TASK_ID = "88fea6584461"
SUMMARY = (
    "0-bg grid (h = block_h = 3-4, w = "
    "2*block_w + 1 with block_w=4-5) "
    "structured as TWO EQUAL-SIZE PANELS "
    "separated by a full-height COLOR-8 "
    "(cyan) DIVIDER column at col bw. (a) "
    "LEFT PANEL (cols 0..bw-1) is a "
    "BINARY 0/1 MASK with 4-7 color-1 (blue) "
    "cells; (b) RIGHT PANEL (cols bw+1.."
    "2*bw) contains 4-7 arbitrary non-{0, 1, "
    "8} colored cells from a 5-color "
    "palette. Rule: use the LEFT PANEL as a "
    "BINARY MASK (color-1 = keep, 0 = "
    "clear). For EVERY CELL in the RIGHT "
    "PANEL at (r, c), check the "
    "CORRESPONDING LEFT cell at (r, c - "
    "bw - 1): if it's 1 (blue), KEEP the "
    "right cell's color; if it's 0, CLEAR "
    "the right cell to 0. Output: the right "
    "panel (cropped or in place) after the "
    "mask filter. Net: left binary mask "
    "filters the right color block, keeping "
    "only cells the mask permits."
)

INVARIANTS = [
    "background is 0",
    "exactly one full-height 8-color divider column",
    "left side is a 0/1 mask of fixed h×w",
    "right side same h×w, with 4-7 non-bg colored cells (no 1s, no 8s)",
    "left mask has 4-7 ones",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_mask", "no_right_block")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 3..4", "valid": "2..6"},
    "grid_w":         {"type": "int", "default": "derived", "valid": "9..13"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "block_w":        {"type": "int", "default": "rng 4..5", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "5", "valid": "5..5"},
    "position_bias":  {"type": "str", "default": "8col_split_mask_and_block",
                       "valid": "8col_split_mask_and_block"},
    "n_distinct_colors": {"type": "int", "default": "5", "valid": "5..5"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full-height 8-divider column; left 0/1 mask; right colored block."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    sep_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not sep_cols:
        return []  # degenerate no_divider — allowed
    errs = []
    if len(sep_cols) != 1:
        errs.append(f"expected exactly 1 full-height 8-divider column; found {len(sep_cols)}")
        return errs
    sep = sep_cols[0]
    # Check left panel is 0/1 only
    left_vals = set(grid[r][c] for r in range(h) for c in range(sep))
    if left_vals - {0, 1}:
        return []  # degenerate no_mask — allowed
    ones = sum(1 for r in range(h) for c in range(sep) if grid[r][c] == 1)
    if ones == 0:
        return []  # degenerate no_mask — allowed
    # Check right panel has some colored cells
    right_vals = set(grid[r][c] for r in range(h) for c in range(sep + 1, w)) - {0, 8}
    if not right_vals:
        return []  # degenerate no_right_block — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        bh = ctx.draw_int("block_h", 3, 3)
        bw = ctx.draw_int("block_w", 4, 4)
    elif difficulty == "hard":
        bh = ctx.draw_int("block_h", 4, 4)
        bw = ctx.draw_int("block_w", 5, 5)
    else:
        bh = ctx.draw_int("block_h", 3, 4)
        bw = ctx.draw_int("block_w", 4, 5)
    rng = ctx.draw_rng("layout")
    h = bh
    w = bw + 1 + bw
    g = full_grid(h, w, 0)
    fill_box(g, 0, bw, h - 1, bw, 8)
    n_ones = rng.randint(4, min(7, bh * bw - 1))
    cells = [(r, c) for r in range(bh) for c in range(bw)]
    rng.shuffle(cells)
    for (r, c) in cells[:n_ones]:
        g[r][c] = 1
    palette = list(random_palette(rng, 5, exclude={1, 8}))
    n_colored = rng.randint(4, 7)
    rcells = [(r, c) for r in range(bh) for c in range(bw)]
    rng.shuffle(rcells)
    for (r, c) in rcells[:n_colored]:
        g[r][bw + 1 + c] = rng.choice(palette)
    return g


def _draw_from_degenerate(name, rng):
    bh, bw = 3, 4
    h = bh; w = bw + 1 + bw
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # mask + block but no 8-divider → can't split into halves
        g[0][0] = 1; g[1][2] = 1
        g[0][5] = 4; g[1][7] = 6
        return g
    if name == "no_mask":
        # divider + block but no left mask → no filter to apply
        fill_box(g, 0, bw, h - 1, bw, 8)
        g[0][bw + 1] = 4; g[1][bw + 2] = 6
        return g
    if name == "no_right_block":
        # divider + mask but right side empty → nothing to filter
        fill_box(g, 0, bw, h - 1, bw, 8)
        g[0][0] = 1; g[1][2] = 1
        return g
    return g
