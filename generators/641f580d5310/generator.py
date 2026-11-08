"""Generator for round3_md:mirror_repair_with_highlighted_fixes — Fill bg cells whose horizontal mirror is color 1, with color 4.

Rule: cell (r, c) bg → 4 if cell (r, w-1-c) is color 1, else 0.
Color-1 cells stay color 1.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_ones,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_ones, ones_at_center_axis, mirror_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "641f580d5310"
VERSION = "1.2.0"  # fixes center-axis 1 leakage on odd widths + self_check
TASK_ID = "641f580d5310"
SUMMARY = "Color-1 cells on left half; output highlights their right-half mirror positions with 4."

# Rivals: 'copy 1 to mirror' refuted by ≥1 demo (mirror is 4, not 1).
# 'mirror with no fill on left' refuted by any demo (1s preserved on
# left). 'mirror to anywhere' refuted by ≥1 demo where the right-half
# pattern is clearly the column-mirror of the left-half.
# 3 demos with varied 1-cell counts and positions cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "between 4 and 7 color-1 cells, all in cols < w/2",
    "right-half corresponding cells are bg (so they get filled with 4)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_ones", "ones_at_center_axis", "mirror_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_ones":         {"type": "int", "default": "rng 4..7", "valid": "2..15"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..2"},
    "position_bias":  {"type": "str", "default": "left_half_ones",
                       "valid": "left_half_ones"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..2"},
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
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 7, 8)
        n_ones = ctx.draw_int("n_ones", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
        n_ones = ctx.draw_int("n_ones", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 7, 10)
        n_ones = ctx.draw_int("n_ones", 4, 7)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    placed = 0
    while placed < n_ones:
        r = rng.randint(0, h - 1)
        c = rng.randint(0, max(0, w // 2 - 1))
        if g[r][c] == 0:
            g[r][c] = 1
            placed += 1
    return g


def self_check(grid, *, difficulty=None, meta=None):
    """Color-1 sources must sit strictly left of the mirror axis with empty partners."""
    errors = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    ones = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 1]
    if not (3 <= len(ones) <= 7):
        errors.append(f"expected 3..7 color-1 cells, got {len(ones)}")
    for r, c in ones:
        if c >= w // 2:
            errors.append(f"color-1 cell at {(r, c)} is not strictly left of the mirror axis")
        mc = w - 1 - c
        if 0 <= mc < w and grid[r][mc] != 0:
            errors.append(f"mirror partner for {(r, c)} is not background")
    bad = sorted({v for row in grid for v in row if v not in (0, 1)})
    if bad:
        errors.append(f"unexpected input colors: {bad}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "no_ones":
        # blank grid → no color-1 cells, mirror has nothing to highlight
        return g
    if name == "ones_at_center_axis":
        # color-1 cells on the center column → mirror lands on themselves; no expansion
        cc = w // 2
        g[1][cc] = 1; g[3][cc] = 1; g[4][cc] = 1
        return g
    if name == "mirror_already_filled":
        # color-1 left + mirror cell already non-zero → predicate "mirror is bg" fails
        g[1][1] = 1; g[1][w - 2] = 6   # mirror cell already non-bg
        g[3][2] = 1; g[3][w - 3] = 7
        return g
    return g
