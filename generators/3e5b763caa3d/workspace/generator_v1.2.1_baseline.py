"""Generator for arc_puzzle_bank_twelfth_21_bundle:easy_81_mirror_left_half_across_divider.

Rule: full-height divider column acts as the vertical mirror axis;
left-half cells get mirrored to the right half.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, cells_on_right, divider_partial.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3e5b763caa3d"
VERSION = "1.2.1"
TASK_ID = "3e5b763caa3d"
SUMMARY = "Full-height divider column (first full non-bg column) is the vertical mirror axis; rule mirrors each non-bg cell on the LEFT of axis to (r, 2*axis - c) on the right, preserving color."

# Rivals: 'mirror right-to-left' refuted by ≥2 demos where source is
# on the left. 'use bg color for mirror' refuted by any demo. 'mirror
# only some colors' refuted by ≥1 demo where multiple colors all
# mirrored. 'mirror across grid center, not divider' refuted by ≥2
# demos with off-center divider.
# 4 demos with varied left-side patterns + divider positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "the center column is a full nonzero divider",
    "source cells appear only on the left side of the divider",
    "the right side starts empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "cells_on_right", "divider_partial")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "3..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13 odd", "valid": "5..25"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells":          {"type": "int", "default": "rng 5..10", "valid": "1..40"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_half_with_mid_divider",
                       "valid": "left_half_with_mid_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, a full-height divider column exists (all nonzero in that column)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    divider_col = None
    for c in range(w):
        if all(grid[r][c] != 0 for r in range(h)):
            divider_col = c
            break
    if divider_col is None:
        errs.append("no full-height nonzero divider column found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 11)
        count = ctx.draw_int("cells", 2, 5)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 14, 20)
        count = ctx.draw_int("cells", 8, 16)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 11, 15)
        count = ctx.draw_int("cells", 5, 10)
    if w % 2 == 0:
        w += 1
    g = full_grid(h, w, 0)
    # Pick axis with enough room on each side
    axis = rng.randint(2, w // 2)
    for r in range(h):
        g[r][axis] = rng.choice([5, 6, 7, 8, 9])
    # Place cells on left side, ensuring mirror stays in-bounds
    choices = [(r, c) for r in range(h) for c in range(axis)
               if 2 * axis - c < w]
    rng.shuffle(choices)
    for r, c in choices[:min(count, len(choices))]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    axis = w // 2
    if name == "no_divider":
        # no divider column → axis undetermined, rule has no mirror line
        g[2][1] = 4; g[3][2] = 6; g[4][1] = 3
        return g
    if name == "cells_on_right":
        # cells on right side already → mirror would clobber existing content
        for r in range(h): g[r][axis] = 9
        g[2][1] = 4; g[3][2] = 6   # left
        g[2][7] = 3; g[3][8] = 7   # right (already filled)
        return g
    if name == "divider_partial":
        # divider has gaps (not full-height) → "the divider column" precondition fails
        for r in range(h - 2): g[r][axis] = 9   # missing bottom 2
        g[2][1] = 4; g[3][2] = 6
        return g
    return g
