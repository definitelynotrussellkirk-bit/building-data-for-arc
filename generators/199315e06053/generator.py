"""Generator for arc_puzzle_bank_21_set9_s:S9_E6.

Rule: count all nonzero dots and emit a bottom-row bar of that length in
the dot color.

Combinatorial axes (8): grid_h/w, palette_kind, dot_count, dot_color,
palette_size, position_bias, n_distinct_colors, texture.
Degenerates: no_dots, count_exceeds_width, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "199315e06053"
VERSION = "1.1.1"
TASK_ID = "199315e06053"
SUMMARY = "Count all nonzero dots and emit a bottom-row bar of that length in the dot color."

INVARIANTS = [
    "background is 0",
    "all nonzero cells share one color",
    "the number of dots is no greater than the grid width",
    "output is a bottom-row bar whose length equals the dot count",
]

PALETTE_KINDS = ("default", "warm", "cool", "rainbow")
DEGENERATE_TEXTURES = ("no_dots", "count_exceeds_width", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "5..15"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "dot_count":      {"type": "int", "default": "rng 2..6", "valid": "1..15"},
    "dot_color":      {"type": "int", "default": "rng",
                       "valid": "2|3|4|6|7|8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: all nonzero cells share one color; count ≤ grid width."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in ("no_dots", "count_exceeds_width", "full_grid"):
        return errs
    nz_vals = [grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz_vals:
        errs.append("no non-zero cells (dots) found")
    else:
        colors = set(nz_vals)
        if len(colors) > 1:
            errs.append(f"all dots should be the same color, got {colors}")
        if len(nz_vals) > w:
            errs.append(f"dot count {len(nz_vals)} exceeds grid width {w}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        count_max = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
        count_max = 6
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 11)
        count_max = 6
    count = min(ctx.draw_int("dot_count", 2, count_max), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    color = rng.choice([2, 3, 4, 6, 7, 8])
    for r, c in rng.sample([(r, c) for r in range(h) for c in range(w)], count):
        g[r][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_dots":
        # zero dots — bar has zero length
        return g
    if name == "count_exceeds_width":
        # count > w — bar can't fit in one row
        for r in range(h - 1):
            for c in range(w):
                g[r][c] = 5
        return g
    if name == "full_grid":
        # every cell is a dot — count = h*w, bar length undefined
        for r in range(h):
            for c in range(w):
                g[r][c] = 4
        return g
    return g
