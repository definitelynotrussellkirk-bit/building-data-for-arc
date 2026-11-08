"""Generator for arc_puzzle_bank_thirteenth21:E85.

Rule: same-color horizontal endpoints with zeros between are bridged.

Combinatorial axes (8): grid_h/w, palette_kind, n_pairs, palette_size,
position_bias, n_distinct_colors, gap_density, texture.
Degenerates: no_gap, single_endpoint, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8f5206e72b74"
VERSION = "2.0.1"
TASK_ID = "8f5206e72b74"
SUMMARY = (
    "0-bg grid (h~6-9, w~"
    "8-13) with 2-4 PAIRS "
    "of SAME-COLOR "
    "ENDPOINTS, each pair "
    "on a DISTINCT ROW. "
    "Each pair: cells at "
    "(r, c0) and (r, c1) "
    "with c1 - c0 ≥ 2 "
    "(gap of ≥1 cell). "
    "Pair colors are "
    "DISTINCT across pairs "
    "from {1..9}. No other "
    "cells. Rule (BRIDGE "
    "SAME-COLOR ENDPOINTS "
    "WITH SOLID LINE): For "
    "EACH ROW r containing "
    "TWO SAME-COLOR "
    "ENDPOINTS at columns "
    "c0 and c1 (c0 < c1): "
    "PAINT every INTERIOR "
    "cell (r, c) with "
    "c0 < c < c1 in the "
    "same color. Endpoints "
    "stay. Net: each "
    "horizontal endpoint "
    "pair becomes a solid "
    "colored line."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "matching endpoints share one row",
    "the cells between matching endpoints are blank",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_gap", "single_endpoint", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "3..18"},
    "grid_w":         {"type": "int", "default": "rng 8..13", "valid": "4..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|varied_palette"},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "gap_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|varied_palette|no_gap|single_endpoint|no_seeds"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: >=1 row contains two same-color cells (horizontal endpoint pair)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in ("no_gap", "single_endpoint", "no_seeds"):
        return errs
    for r in range(h):
        seen: dict[int, int] = {}
        for c in range(w):
            v = grid[r][c]
            if v == 0:
                continue
            if v in seen and seen[v] != c:
                return errs  # found a valid pair
            seen[v] = c
    errs.append("no row contains a same-color pair of endpoint cells")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 8, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 11, 13)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 8, 13)
    target = min(ctx.draw_int("pairs", 2, 4), h, 9)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), target)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], target)
    for r, color in zip(rows, colors):
        c0 = rng.randint(0, w - 3)
        c1 = rng.randint(c0 + 2, w - 1)
        g[r][c0] = color
        g[r][c1] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "no_gap":
        # touching endpoints — interval has zero interior
        g[2][3] = 4
        g[2][4] = 4
        return g
    if name == "single_endpoint":
        # single cell, no second endpoint
        g[3][5] = 6
        return g
    if name == "no_seeds":
        # empty grid — nothing to bridge
        return g
    return g
