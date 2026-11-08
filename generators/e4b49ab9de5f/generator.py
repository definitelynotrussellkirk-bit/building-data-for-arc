"""Generator for arc_puzzle_bank_seventeenth_21_bundle:easy_115_top_pack_each_column.

Combinatorial axes (8): grid_h, grid_w, palette_kind, columns,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: already_top_packed, no_active_columns, single_cell_column.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e4b49ab9de5f"
VERSION = "2.2.0"  # clean but small grids (7-10) and 3-6 columns. Rule packs each column independently -> widen grids, active-column count (axis 1-12) and cells-per-column for more positions/sizes.
TASK_ID = "e4b49ab9de5f"
SUMMARY = (
    "0-bg grid (h×w, ~7-10 by ~6-10) with 3-6 'active' columns. "
    "Each active column has 1-3 SCATTERED non-zero cells at "
    "various rows (NOT all at the top — at least one cell below "
    "the top row). Cells use random colors. Inactive columns are "
    "entirely 0. Rule: for each column c independently, collect "
    "all non-zero values top-to-bottom (preserving order). Pack "
    "them at the TOP of the column starting at row 0. Remaining "
    "cells become 0. Equivalent to upward gravity."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "3-6 active columns each with 1-3 non-zero cells",
    "at least one cell is below the top row (so packing visibly moves cells)",
    "columns transform independently (no cross-column movement)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("already_top_packed", "no_active_columns", "single_cell_column")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "columns":        {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "below_top_row",
                       "valid": "below_top_row"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..6", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 6, 8)
        target = min(ctx.draw_int("columns", 3, 4), w)
        cmax = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 11, 16)
        target = min(ctx.draw_int("columns", 6, 10), w)
        cmax = 5
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 8, 12)
        target = min(ctx.draw_int("columns", 4, 7), w)
        cmax = 4
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c in rng.sample(range(w), target):
        count = rng.randint(1, min(cmax, h - 1))
        for r in sorted(rng.sample(range(1, h), count)):
            g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate a visible per-column upward-packing instance."""
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["expected a nonempty rectangular grid"]
    h, w = len(grid), len(grid[0])
    vals = {v for row in grid for v in row}
    bad = sorted(v for v in vals if not isinstance(v, int) or v < 0 or v > 9)
    if bad:
        errs.append(f"cell values outside ARC palette: {bad}")
    active = [c for c in range(w) if any(grid[r][c] != 0 for r in range(h))]
    if not active:
        errs.append("expected at least one active column")
    if len(active) < 3:
        errs.append(f"expected at least three active columns in normal samples, got {len(active)}")
    if len(active) > 12:
        errs.append(f"too many active columns for declared axis: {len(active)}")
    if any(grid[0][c] != 0 for c in active):
        errs.append("normal samples should start with active cells below the top row, not already packed")
    if not any(r > 0 and grid[r][c] != 0 for c in active for r in range(h)):
        errs.append("no below-top nonzero cell, so packing would not visibly move anything")
    for c in active:
        count = sum(1 for r in range(h) if grid[r][c] != 0)
        if count < 1 or count > 5:
            errs.append(f"column {c} has {count} nonzero cells outside expected 1..5 range")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "already_top_packed":
        # values already sit at the top → packing is identity, no visible movement
        for c in range(0, w, 2):
            g[0][c] = 4
            if c + 1 < w:
                g[1][c] = 5
        return g
    if name == "no_active_columns":
        # empty grid → no values to pack, rule no-op
        return g
    if name == "single_cell_column":
        # each column has at most one cell → packing reduces to top-row presence test
        for c in [1, 4, 6]:
            g[c][c] = 1 + (c % 5)
        return g
    return g
