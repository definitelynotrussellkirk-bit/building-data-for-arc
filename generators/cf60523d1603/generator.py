"""Generator for arc_puzzle_bank_21_next:easy_c06.

Rule: for each col, for each color, if exactly 2 cells have that color
and the cells between them are all 0 → fill the segment with the color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_columns,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, three_cells_per_color, blocked_between.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cf60523d1603"
VERSION = "1.2.0"  # identity fix: when both sampled rows were adjacent (gap<2) no pair was placed; all-columns-failing left a blank grid -> rule fills nothing -> identity. Now retry per column for a >=2 gap and guarantee >=1 fillable pair.
TASK_ID = "cf60523d1603"
SUMMARY = "2-3 columns each have exactly 2 cells of one color (all-0 between)."

INVARIANTS = [
    "≥2 cols have exactly 2 cells of one color, with ≥2 0-cells between",
    "colors across cols may differ",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "three_cells_per_color", "blocked_between")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_columns":      {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "position_bias":  {"type": "str", "default": "col_endpoints",
                       "valid": "col_endpoints"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..3", "valid": "1..5"},
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
        w = ctx.draw_int("grid_w", 5, 6)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 5, 7)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    cols = rng.sample(range(w), rng.randint(2, 3))
    palette = [2, 3, 4, 5, 6, 7, 8, 9]
    placed = 0
    for c in cols:
        color = rng.choice(palette)
        # Need a same-color pair with >=1 zero between -> the rule fills the
        # segment. If the two sampled rows are adjacent (gap 1) NOTHING is placed;
        # if every column fails the grid stays blank -> no fill -> identity demo.
        # Retry until the gap is >= 2 so this column is fillable.
        for _ in range(20):
            rs = sorted(rng.sample(range(h), 2))
            if rs[1] - rs[0] >= 2:
                g[rs[0]][c] = color; g[rs[1]][c] = color
                placed += 1
                break
    if placed == 0:
        # guarantee at least one fillable pair (rows 0 and h-1, gap >= 2)
        c = cols[0]
        g[0][c] = palette[0]; g[h - 1][c] = palette[0]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """At least one column must hold exactly two same-color cells with >=1
    zero between them, else the rule fills nothing (identity demo)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h = len(grid); w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    for c in range(w):
        from collections import Counter
        col = [grid[r][c] for r in range(h)]
        for color, cnt in Counter(v for v in col if v != 0).items():
            if cnt == 2:
                rs = [r for r in range(h) if grid[r][c] == color]
                if all(grid[r][c] == 0 for r in range(rs[0] + 1, rs[1])) \
                        and rs[1] - rs[0] >= 2:
                    return []
    return ["no fillable column pair: rule is a no-op"]


def _draw_from_degenerate(name, rng):
    h, w = 6, 6
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # nonzero cells exist but never form an aligned same-color pair → no fill
        g[1][1] = 3
        g[3][3] = 5
        g[5][2] = 6
        return g
    if name == "three_cells_per_color":
        # column has 3 cells of one color → "exactly 2" condition violated
        g[0][2] = 4; g[3][2] = 4; g[5][2] = 4
        return g
    if name == "blocked_between":
        # column has 2 same-color endpoints but a non-0 between → fill blocked
        g[0][3] = 6; g[5][3] = 6
        g[2][3] = 7
        return g
    return g
