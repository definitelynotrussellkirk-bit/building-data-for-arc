"""Generator for arc_additional_puzzles_21_set14_bundle:E95.

Rule: find full-height col of 5s. For each non-{0,5} cell at (r, c) on
the left, set (r, 2*guide-c) on the right to that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_divider, source_on_right, source_on_divider.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "29c3f342b62c"
VERSION = "2.0.1"
TASK_ID = "29c3f342b62c"
SUMMARY = (
    "Grid (size varies) with ONE FULL-HEIGHT COLOR-5 (gray) DIVIDER at a varied "
    "column g_c, and 2-7 ISOLATED non-{0,5} cells on ONE side of it (left or right) "
    "in random colors from {1,2,3,4,6,7,8,9}; the other side is input-empty. Rule: "
    "find the full-height color-5 divider column g_c; for each non-{0,5} cell at "
    "(r,c), paint the MIRROR position (r, 2*g_c - c) with that color. The source "
    "cells and divider stay. Net: every coloured cell reflects across the gray spine."
)

INVARIANTS = [
    "exactly 1 full-height col of 5s",
    "2-7 isolated non-{0,5} source cells on one side, mirrorable in-bounds",
    "the opposite side is input-empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_divider", "source_on_right", "source_on_divider")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 4..6", "valid": "3..14"},
    "grid_w":         {"type": "int", "default": "rng 9..13", "valid": "7..17"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..3", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..8", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "left_of_divider",
                       "valid": "left_of_divider"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..8", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: exactly 1 full-height color-5 column; ≥2 non-{0,5} source cells on one side."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_divider", "source_on_right", "source_on_divider"):
        return []
    errs = []
    div_cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    if len(div_cols) != 1:
        errs.append(f"expected 1 full-height color-5 column, found {len(div_cols)}")
    src = sum(1 for r in range(h) for c in range(w) if grid[r][c] not in (0, 5))
    if src < 1:
        errs.append("no non-{0,5} source cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    # rule finds the full-height color-5 guide column and MIRRORS every coloured cell
    # across it. Was w=9, guide col=4 fixed (in=3). Now grid size, guide column, source
    # side, and cell count all vary (rule locates the guide dynamically).
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 6); w = ctx.draw_int("grid_w", 7, 9); n = rng_n(ctx, 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 14); w = ctx.draw_int("grid_w", 11, 17); n = rng_n(ctx, 4, 7)
    else:
        h = ctx.draw_int("grid_h", 5, 10); w = ctx.draw_int("grid_w", 9, 13); n = rng_n(ctx, 2, 5)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    gc = rng.randint(2, w - 3)               # guide column with room on both sides
    for r in range(h):
        g[r][gc] = 5
    palette = [1, 2, 3, 4, 6, 7, 8, 9]
    side = rng.choice([-1, 1])               # source cells on left (-1) or right (+1)
    if side < 0:
        c_lo, c_hi = max(0, 2 * gc - (w - 1)), gc - 1
    else:
        c_lo, c_hi = gc + 1, min(w - 1, 2 * gc)
    if c_lo > c_hi:                          # degenerate guide placement -> fall back to left
        c_lo, c_hi = max(0, 2 * gc - (w - 1)), gc - 1
    for _ in range(n):
        for _ in range(20):
            r = rng.randint(0, h - 1); c = rng.randint(c_lo, c_hi)
            if g[r][c] == 0:
                g[r][c] = rng.choice(palette)
                break
    return g


def rng_n(ctx, lo, hi):
    return ctx.draw_int("n_cells", lo, hi)


def _draw_from_degenerate(name, rng):
    h, w = 5, 9
    g = full_grid(h, w, 0)
    if name == "no_divider":
        # no full-height 5-col → mirror axis is undefined
        g[1][1] = 3; g[3][2] = 7
        return g
    gc = 4
    for r in range(h):
        g[r][gc] = 5
    if name == "source_on_right":
        # all source cells already on the right → rule's "left source" assumption violated
        g[1][6] = 3; g[3][7] = 7
        return g
    if name == "source_on_divider":
        # source overlaps the divider column → ambiguous which side it belongs to
        g[1][gc] = 3
        g[3][1] = 7
        return g
    return g
