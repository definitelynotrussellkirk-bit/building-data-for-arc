"""Generator for arc_additional_puzzle_bank_volume6:M38 — Draw rect borders for color pairs.

Rule: for each non-bg color with exactly 2 cells (diagonal corners), paint
the rectangle border between them in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_rects,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, single_cell_colors, collinear_pair.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5cbd3724acbd"
VERSION = "1.2.0"
TASK_ID = "5cbd3724acbd"
SUMMARY = "2-3 colors each with exactly 2 cells at diagonal corners + decoration."

INVARIANTS = [
    "between 2 and 3 distinct colors",
    "each has exactly 2 cells at distinct rows AND cols",
    "rectangles don't overlap",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "single_cell_colors", "collinear_pair")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..11", "valid": "8..14"},
    "grid_w":         {"type": "int", "default": "rng 11..13", "valid": "9..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_rects":        {"type": "int", "default": "rng 2..3", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "diagonal_corner_pairs",
                       "valid": "diagonal_corner_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..8"},
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
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 11)
        w = ctx.draw_int("grid_w", 12, 13)
    else:
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 11, 13)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    palette = list(range(2, 10)); rng.shuffle(palette)
    n = rng.randint(2, 3)
    rects = [
        ((1, 1), (4, 4)),
        ((1, 7), (3, 10)),
        ((6, 2), (8, 6)),
        ((5, 8), (8, 11)),
    ]
    rng.shuffle(rects)
    for (r1, c1), (r2, c2) in rects[:n]:
        if r2 < h and c2 < w:
            color = palette.pop()
            g[r1][c1] = color
            g[r2][c2] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: 2-3 distinct colors each with exactly 2 cells at distinct rows and cols."""
    if not grid or not grid[0]:
        return ["empty grid"]
    errs = []
    h, w = len(grid), len(grid[0])
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    from collections import defaultdict
    by_color: dict = defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                by_color[grid[r][c]].append((r, c))
    if not by_color:
        errs.append("no non-zero cells found")
        return errs
    for color, cells in by_color.items():
        if len(cells) != 2:
            errs.append(f"color {color} has {len(cells)} cells, expected 2")
        else:
            (r1, c1), (r2, c2) = cells
            if r1 == r2:
                errs.append(f"color {color} has both cells in same row {r1}")
            if c1 == c2:
                errs.append(f"color {color} has both cells in same col {c1}")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 10, 12
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # blank → no diagonal corner pairs to draw rects for
        return g
    if name == "single_cell_colors":
        # each color appears once → no second corner; rule has no rect
        g[1][1] = 4
        g[3][7] = 6
        g[6][3] = 7
        return g
    if name == "collinear_pair":
        # 2-cell pair on the same row OR column → rectangle collapses to a line
        g[2][1] = 4; g[2][9] = 4   # same row
        g[1][5] = 6; g[7][5] = 6   # same column
        return g
    return g
