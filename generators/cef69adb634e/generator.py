"""Generator for arc_additional_puzzle_bank_volume23:M156.

Rule: for each color in {2, 3, 4}, if there are exactly 2 cells at
diagonal corners (different rows AND cols), paint the rect border in
that color.

Combinatorial axes (8): grid_h/w, palette_kind, n_pair_colors,
palette_size, position_bias, n_distinct_colors, rect_size, texture.
Degenerates: only_one_pair_color, cells_aligned, no_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cef69adb634e"
VERSION = "2.0.1"
TASK_ID = "cef69adb634e"
SUMMARY = (
    "0-bg grid (h~9-11, w~"
    "13-15) with: (a) FOR "
    "EACH of colors {2, 3, 4}, "
    "EXACTLY 2 CELLS placed at "
    "DISTINCT ROWS AND "
    "DISTINCT COLUMNS (i.e., "
    "diagonal corners of a "
    "rectangle); (b) 1-4 DECOY "
    "cells in colors from {1, "
    "5, 6, 7, 8, 9} at random "
    "empty positions. Each "
    "color may overlap "
    "rectangles but rectangle-"
    "outline paths can clobber "
    "decor — that's fine. "
    "Rule (PAINT RECT OUTLINES "
    "BETWEEN DIAGONAL CORNER "
    "PAIRS): For EACH color "
    "C ∈ {2, 3, 4}: if C has "
    "exactly 2 cells at "
    "(r1, c1) and (r2, c2) "
    "with r1 ≠ r2 AND c1 ≠ c2, "
    "PAINT the RECTANGLE "
    "OUTLINE through those 2 "
    "corners in color C — "
    "outline = top row, "
    "bottom row, left col, "
    "right col of the bbox "
    "(min, max)(rows/cols). "
    "Interior of the rect "
    "stays. Other colors "
    "(non-{2, 3, 4}) "
    "untouched. Net: each "
    "diagonal pair in 2/3/4 "
    "becomes a hollow "
    "rectangle outline."
)

# Rivals: 'paint solid rect interior' refuted by ≥1 demo where output
# is hollow. 'apply only to color 2' refuted by ≥2 demos with all
# three colors visible as outlines. 'apply to all colors' refuted by
# ≥1 demo with non-{2,3,4} cells left untouched. 'use diagonal line
# instead of rect outline' refuted by any demo showing the rect.
# 4 demos with varied corner positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "each of colors 2, 3, 4 has exactly 2 cells at distinct rows AND cols",
    "rectangles don't fully overlap (some independence)",
    "decoration is non-{2,3,4} cells",
]

PALETTE_KINDS = ("default", "tight_rects", "wide_rects", "diagonal_rects")
DEGENERATE_TEXTURES = ("only_one_pair_color", "cells_aligned", "no_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..16"},
    "grid_w":         {"type": "int", "default": "rng 13..15", "valid": "10..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pair_colors":  {"type": "int", "default": "3", "valid": "3"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "rect_size":      {"type": "str", "default": "fixed", "valid": "fixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each of colors 2/3/4 appears exactly 0 or 2 times."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if any(v < 0 or v > 9 for row in grid for v in row):
        errs.append("cell value out of 0-9")
        return errs
    from collections import Counter
    counts = Counter(v for row in grid for v in row if v != 0)
    for c in (2, 3, 4):
        n = counts.get(c, 0)
        if n not in (0, 2):
            errs.append(f"color {c} appears {n} times; expected 0 or 2")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 10, 13)
        n_pair_colors = rng.randint(1, 2)
        n_decor = rng.randint(0, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 16, 20)
        n_pair_colors = 3
        n_decor = rng.randint(3, 6)
    else:
        h = ctx.draw_int("grid_h", 10, 13)
        w = ctx.draw_int("grid_w", 13, 17)
        n_pair_colors = rng.randint(2, 3)
        n_decor = rng.randint(1, 4)
    g = full_grid(h, w, 0)
    pair_colors = [2, 3, 4][:n_pair_colors]
    for color in pair_colors:
        for _ in range(40):
            r1 = rng.randint(0, h - 1); r2 = rng.randint(0, h - 1)
            c1 = rng.randint(0, w - 1); c2 = rng.randint(0, w - 1)
            if r1 == r2 or c1 == c2:
                continue
            if g[r1][c1] != 0 or g[r2][c2] != 0:
                continue
            # Avoid the cell at (r1, c2) or (r2, c1) being non-bg too —
            # the rule will paint the rect outline so other cells along
            # the outline that already have non-bg might be overwritten.
            # That's fine for diversity.
            g[r1][c1] = color
            g[r2][c2] = color
            break
    # Decoration cells in colors NOT in {2, 3, 4}, NOT in {0}.
    decor_pool = [1, 5, 6, 7, 8, 9]
    rng.shuffle(decor_pool)
    placed = 0
    for _ in range(80):
        if placed >= n_decor:
            break
        r = rng.randint(0, h - 1); c = rng.randint(0, w - 1)
        if g[r][c] != 0:
            continue
        g[r][c] = decor_pool[placed % len(decor_pool)]
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 14
    g = full_grid(h, w, 0)
    if name == "only_one_pair_color":
        # only color 2 has a diagonal pair — colors 3, 4 are missing
        g[1][1] = 2; g[6][8] = 2
        g[5][5] = 7
        return g
    if name == "cells_aligned":
        # color 2 cells are in same row → not a diagonal corner pair
        g[3][1] = 2; g[3][8] = 2
        g[2][10] = 3; g[5][12] = 3
        g[7][2] = 4; g[8][9] = 4
        return g
    if name == "no_pairs":
        # only decoration, no pairs of {2,3,4}
        g[2][2] = 7
        g[5][6] = 7
        return g
    return g
