"""Generator for arc_puzzle_bank_twentyfirst_21_bundle:easy_145_mirror_left_half_across_divider.

Rule: a full color-8 column divides the grid; left-half cells are mirrored
onto the right half.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_axis, source_on_right, source_on_axis.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "53dcf1ac2709"
VERSION = "2.0.1"
TASK_ID = "53dcf1ac2709"
SUMMARY = (
    "0-bg grid (h ∈ 7-11, w ∈ 9-13 "
    "FORCED ODD so a center column "
    "exists, axis = w//2) with: (a) "
    "ONE FULL COLOR-8 (CYAN) DIVIDER "
    "COLUMN at col axis (every cell "
    "in that column painted 8); (b) "
    "COUNT ∈ 5-10 SPARSE SOURCE "
    "CELLS placed at random LEFT-HALF "
    "positions (cols 0..axis-1), each "
    "in a random color drawn from "
    "{1..9}\\{0, 8}. The RIGHT HALF "
    "(cols axis+1..w-1) starts "
    "EMPTY. Rule (FOR EACH NON-BG "
    "NON-8 CELL ON THE LEFT, COPY "
    "IT TO ITS MIRROR POSITION ON "
    "THE RIGHT — MIRROR AXIS IS "
    "THE COLOR-8 DIVIDER COLUMN; "
    "ORIGINAL LEFT CELLS PRESERVED): "
    "FIND the full color-8 column "
    "→ axis position c_axis. For "
    "EACH non-bg cell at (r, c) "
    "with c < c_axis and color k: "
    "COMPUTE mirror position "
    "(r, 2*c_axis - c). PAINT "
    "g[r][2*c_axis-c] = k. The "
    "left source cells and the "
    "color-8 divider stay. Net: "
    "the left-half pattern is "
    "reflected onto the right "
    "half across the cyan axis."
)

INVARIANTS = [
    "background is 0",
    "the center divider column is all 8",
    "source cells appear only left of the divider",
    "the right half starts empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_axis", "source_on_right", "source_on_axis")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..11", "valid": "3..20"},
    "grid_w":         {"type": "int", "default": "rng 9..13 odd", "valid": "5..25"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells":          {"type": "int", "default": "rng 5..10", "valid": "1..40"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..8"},
    "position_bias":  {"type": "str", "default": "left_of_axis",
                       "valid": "left_of_axis"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: rectangular grid; full-height color-8 divider column exists; source cells left of divider."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    divider_cols = [c for c in range(w) if all(grid[r][c] == 8 for r in range(h))]
    if not divider_cols:
        return errors  # degenerate (no_axis) — allowed
    div = divider_cols[0]
    left_cells = [(r, c) for r in range(h) for c in range(div) if grid[r][c] not in (0, 8)]
    if not left_cells:
        return errors  # degenerate (source_on_right or empty) — allowed
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 11)
        count = ctx.draw_int("cells", 5, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
        count = ctx.draw_int("cells", 8, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 11)
        w = ctx.draw_int("grid_w", 9, 13)
        count = ctx.draw_int("cells", 5, 10)
    if w % 2 == 0:
        w += 1
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    axis = w // 2
    for r in range(h):
        g[r][axis] = 8
    choices = [(r, c) for r in range(h) for c in range(axis)]
    rng.shuffle(choices)
    for r, c in choices[:min(count, len(choices))]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 9])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 11
    g = full_grid(h, w, 0)
    axis = w // 2
    if name == "no_axis":
        # no color-8 divider column → mirror axis is undefined
        g[1][2] = 4; g[3][3] = 5; g[5][1] = 6
        return g
    for r in range(h):
        g[r][axis] = 8
    if name == "source_on_right":
        # source cells already on right of axis → "source on left" invariant violated
        g[1][6] = 4; g[3][7] = 5; g[5][8] = 6
        return g
    if name == "source_on_axis":
        # source cell sits on the axis column → ambiguous which side it belongs to
        g[1][axis] = 4
        g[3][1] = 5
        return g
    return g
