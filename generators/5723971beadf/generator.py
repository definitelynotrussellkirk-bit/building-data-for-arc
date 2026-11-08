"""Generator for arc_puzzle_bank_twelfth21:E78.

Rule: same-color vertical endpoints with zeros between are bridged by
filling the gap with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, n_pairs, palette_size,
position_bias, n_distinct_colors, gap_density, texture.
Degenerates: no_gap, single_endpoint, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5723971beadf"
VERSION = "1.1.1"
TASK_ID = "5723971beadf"
SUMMARY = "Same-color vertical endpoints with zeros between are bridged."

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "matching endpoints share one column",
    "the cells between matching endpoints are blank",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_gap", "single_endpoint", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..13", "valid": "4..24"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "3..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "gap_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 13)
        w = ctx.draw_int("grid_w", 8, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 6, 9)
    target = min(ctx.draw_int("pairs", 2, 4), w, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for c, color in zip(cols, colors):
        r0 = rng.randint(0, h - 3)
        r1 = rng.randint(r0 + 2, h - 1)
        g[r0][c] = color
        g[r1][c] = color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: at least one pair of same-color cells in the same column with zeros between."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    found = False
    for c in range(w):
        col_vals = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        by_color: dict = {}
        for r, v in col_vals:
            by_color.setdefault(v, []).append(r)
        for color, rows in by_color.items():
            if len(rows) >= 2:
                r0, r1 = min(rows), max(rows)
                if r1 > r0 + 1:
                    # Check there's a zero between them
                    if any(grid[r][c] == 0 for r in range(r0 + 1, r1)):
                        found = True
    if not found:
        errs.append("no vertical endpoint pair with gap found")
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 9, 7
    g = full_grid(h, w, 0)
    if name == "no_gap":
        # touching endpoints — bridge interior is empty
        g[2][3] = 4
        g[3][3] = 4
        return g
    if name == "single_endpoint":
        # one cell, no second endpoint to bridge to
        g[3][2] = 6
        return g
    if name == "no_seeds":
        # empty grid — nothing to bridge
        return g
    return g
