"""Generator for arc_puzzle_bank_fourteenth_21_bundle:easy_93_fill_vertical_intervals.

Rule: place same-color endpoint pairs in separate columns; output fills
each column's interval inclusively.

Combinatorial axes (8): grid_h, grid_w, palette_kind, segments,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cdc2954e8f80"
VERSION = "1.1.1"
TASK_ID = "cdc2954e8f80"
SUMMARY = "Place same-color endpoint pairs in separate columns for vertical interval filling."

INVARIANTS = [
    "background is 0",
    "each active column contains one same-color endpoint pair",
    "the endpoints in each column have at least one blank cell between them",
    "active endpoint colors are distinct across the grid",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..12", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "segments":       {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "col_endpoint_pairs",
                       "valid": "col_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; each non-zero color appears exactly twice (endpoint pairs)."""
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
    bad = [(c, n) for c, n in counts.items() if n != 2]
    if bad:
        errs.append(f"colors not appearing exactly twice: {bad[:5]}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 7, 8)
        target = min(ctx.draw_int("segments", 2, 2), w, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 12)
        w = ctx.draw_int("grid_w", 9, 10)
        target = min(ctx.draw_int("segments", 3, 4), w, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 7, 10)
        target = min(ctx.draw_int("segments", 2, 4), w, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for c, color in zip(cols, colors):
        r1 = rng.randint(0, h - 3)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = color
        g[r2][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 10, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair to fill span between
        g[2][1] = 4
        g[6][3] = 6
        return g
    if name == "mismatched_endpoints":
        # mismatched col endpoints
        g[1][1] = 4; g[6][1] = 6
        g[2][3] = 3; g[7][3] = 7
        return g
    if name == "span_already_filled":
        # span already filled in column
        for r in range(1, 7): g[r][1] = 4
        g[1][3] = 6; g[3][3] = 9; g[5][3] = 6
        return g
    return g
