"""Generator for arc_additional_puzzle_bank_volume2:M10.

Rule: for each non-bg color that has exactly 2 cells in the input, fill the
solid rectangle between them (treating them as diagonal corners) with that
color. Other colors and cells unchanged.

Combinatorial axes (8): grid_h/w, palette_kind, n_pairs, palette_size,
position_bias, n_distinct_colors, rect_orientation, texture.
Degenerates: single_cell_color, three_cell_color, overlapping_rects.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3a8b7b814eb5"
VERSION = "2.0.1"
TASK_ID = "3a8b7b814eb5"
SUMMARY = (
    "0-bg grid (h~7-18, w~8-20) with 2-5 PAIRS "
    "(one pair per distinct color). For EACH "
    "PAIR: pick a color from a shuffled palette "
    "of n_pairs distinct values from {1..9}, "
    "pick two cells at OPPOSITE DIAGONAL "
    "CORNERS of an axis-aligned rectangle: top-"
    "left (r1, c1) and bottom-right (r2, c2) "
    "where r2 > r1 and c2 > c1. The bbox "
    "rectangles do NOT overlap (overlap check "
    "via _bb_overlap). Place these 2 cells in "
    "the chosen color; the rest of each "
    "rectangle's interior + border are bg-0. "
    "Each color appears at exactly 2 cells. "
    "Rule (FOR EACH COLOR WITH EXACTLY 2 CELLS, "
    "FILL THE SOLID RECTANGLE BETWEEN THEM "
    "TREATING THEM AS DIAGONAL CORNERS): for "
    "EACH non-bg COLOR in the grid: COUNT its "
    "occurrences. IF count = 2 AND the two "
    "cells are at distinct rows AND distinct "
    "columns (forming diagonal corners of a "
    "non-degenerate rectangle): COMPUTE the "
    "bbox (r1, c1, r2, c2) from the two corner "
    "positions. FILL every cell (r, c) with "
    "r1 ≤ r ≤ r2 AND c1 ≤ c ≤ c2 with the "
    "pair's color. Colors with count ≠ 2 or "
    "with axis-aligned cells stay unchanged. "
    "Net: each color-pair grows into a solid "
    "filled rectangle."
)

# Rivals: 'output is input' refuted by any demo (rectangles fill).
# 'fill only one color' refuted by ≥2 demos with ≥2 paired colors.
# 'use bg/different color for fill' refuted by any demo (fill = pair color).
# 'fill 1-cell colors with single dot rect' refuted by any demo.
# 3 demos with varied pairs cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "between 2 and 4 distinct non-bg colors",
    "each has exactly 2 cells, at diagonal corners (different rows AND cols)",
    "rectangles are non-overlapping",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_cell_color", "three_cell_color", "overlapping_rects")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "6..18"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "7..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "position_bias":  {"type": "str", "default": "non_overlapping",
                       "valid": "non_overlapping"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "2..5"},
    "rect_orientation": {"type": "str", "default": "diagonal", "valid": "diagonal"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _bb_overlap(b1, b2):
    r1, c1, r2, c2 = b1
    R1, C1, R2, C2 = b2
    return not (r2 < R1 or R2 < r1 or c2 < C1 or C2 < c1)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each active nonzero color appears exactly 2 times (diagonal corner pair)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    from collections import Counter
    counts = Counter(grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0)
    if not counts:
        pass  # degenerate — allowed
    else:
        for color, cnt in counts.items():
            if cnt != 2:
                errors.append(f"color {color} has {cnt} cells, expected exactly 2 (diagonal pair)")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 11)
        n_pairs = ctx.draw_int("n_pairs", 1, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 15, 20)
        n_pairs = ctx.draw_int("n_pairs", 3, 5)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 11, 15)
        n_pairs = ctx.draw_int("n_pairs", 2, 3)
    g = full_grid(h, w, 0)
    palette = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n_pairs)
    bboxes = []
    placed = 0
    for color in palette:
        for _ in range(80):
            r1 = rng.randint(0, h - 2); c1 = rng.randint(0, w - 2)
            r2 = rng.randint(r1 + 1, h - 1); c2 = rng.randint(c1 + 1, w - 1)
            bb = (r1, c1, r2, c2)
            if any(_bb_overlap(bb, ob) for ob in bboxes): continue
            g[r1][c1] = color
            g[r2][c2] = color
            bboxes.append(bb)
            placed += 1
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 11
    g = full_grid(h, w, 0)
    if name == "single_cell_color":
        g[1][1] = 1
        g[h - 3][2] = 3; g[h - 1][5] = 3
        return g
    if name == "three_cell_color":
        g[1][1] = 1; g[3][5] = 1; g[2][3] = 1
        g[h - 3][2] = 3; g[h - 1][5] = 3
        return g
    if name == "overlapping_rects":
        g[1][1] = 1; g[5][7] = 1
        g[2][3] = 3; g[6][9] = 3
        return g
    return g
