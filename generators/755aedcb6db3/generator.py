"""Generator for v2_meta_puzzles:M5 — vertical 5-divider mirror.

Rule: a vertical color-5 column splits the grid. Non-{0, 5} cells are
mirrored across the divider (col-distance preserved).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, no_cells, cells_on_both_sides.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "755aedcb6db3"
VERSION = "1.1.1"
TASK_ID = "755aedcb6db3"
SUMMARY = "Full color-5 vertical column + 2-4 color cells on one side."

INVARIANTS = [
    "background is 0",
    "exactly one full color-5 column (the divider)",
    "left of divider has 2-4 sparse non-{0, 5} cells; right of divider is bg",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "no_cells", "cells_on_both_sides")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..8", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly one full-height color-5 divider column, ≥1 non-{0,5} cell on one side."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        return [f"grid too large: {h}x{w}"]
    errs = []
    # Find full color-5 columns
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(div_cols) != 1:
        errs.append(f"expected exactly 1 full color-5 divider column, got {len(div_cols)}")
        return errs
    # At least one non-{0,5} cell
    cells = any(grid[r][c] not in (0, 5) for r in range(h) for c in range(w))
    if not cells:
        errs.append("no non-{0,5} cells found (nothing to mirror)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 6)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 8)
        w = ctx.draw_int("grid_w", 8, 10)
    rng = ctx.draw_rng("layout")

    g = full_grid(h, w, 0)
    div = rng.randint(2, w - 4)
    for r in range(h):
        g[r][div] = 5
    for _ in range(rng.randint(2, 4)):
        for _t in range(40):
            r = rng.randint(0, h - 1); c = rng.randint(0, div - 1)
            if g[r][c] != 0: continue
            mc = 2 * div - c
            if not (0 <= mc < w): continue
            g[r][c] = rng.choice([1, 2, 3, 4, 6, 7, 8, 9])
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # cells but no 5-divider → no axis to mirror across
        g[2][1] = 4; g[3][2] = 6; g[4][1] = 7
        return g
    if name == "no_cells":
        # divider but empty side → nothing to reflect
        for r in range(h): g[r][4] = 5
        return g
    if name == "cells_on_both_sides":
        # cells on both sides of divider → reflection collides with existing cells
        for r in range(h): g[r][4] = 5
        g[2][1] = 4; g[3][2] = 6
        g[2][7] = 5; g[3][6] = 7  # opposite side already occupied
        return g
    return g
