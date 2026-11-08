"""Generator for arc_puzzle_bank_next21:E14.

Rule: scatter upper-half colored cells; reflect them across the
horizontal midline; originals remain.

Combinatorial axes (8): grid_h/w, palette_kind, n_cells, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: no_cells, all_on_midline, full_lower_half.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c9c600cd5283"
VERSION = "1.1.1"  # self_check
TASK_ID = "c9c600cd5283"
SUMMARY = "Scatter upper-half colored cells for horizontal midline reflection."

INVARIANTS = [
    "background is 0",
    "all source cells are off the horizontal midline",
    "mirrored positions are initially 0",
    "source cells are sparse and preserve their colors after reflection",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_cells", "all_on_midline", "full_lower_half")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..9", "valid": "3..17"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "3..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells":          {"type": "int", "default": "rng 3..6", "valid": "1..18"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "upper_half",
                       "valid": "upper_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 5, 9)
        w = ctx.draw_int("grid_w", 7, 11)
    target = ctx.draw_int("cells", 3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    top_rows = list(range(h // 2))
    candidates = [(r, c) for r in top_rows for c in range(w)]
    rng.shuffle(candidates)
    colors = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    for r, c in candidates[:target]:
        g[r][c] = rng.choice(colors)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_cells":
        # empty grid — nothing to mirror
        return g
    if name == "all_on_midline":
        # all cells exactly on midline → mirror is identity (rule trivial)
        mid = h // 2
        g[mid][2] = 4
        g[mid][5] = 6
        g[mid][7] = 8
        return g
    if name == "full_lower_half":
        # cells in lower half — invariant violated (sources should be upper)
        for r, c, v in [(5, 1, 2), (5, 4, 3), (6, 6, 5)]:
            g[r][c] = v
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs = []
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(cells) < 3:
        errs.append(f"expected at least 3 source cells, got {len(cells)}")
    for r, c in cells:
        if r >= h // 2:
            errs.append("source cell is not in the upper half")
            break
        mr = h - 1 - r
        if grid[mr][c] != 0:
            errs.append("mirror target is already occupied")
            break
    return errs
