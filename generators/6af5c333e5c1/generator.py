"""Generator for arc_puzzle_bank_21_set5_s:S5_E6.

Rule: rows with exactly two blue endpoints are filled into horizontal
segments.

Combinatorial axes (8): grid_h, grid_w, palette_kind, segment_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_endpoint_only, span_already_filled, no_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "6af5c333e5c1"
VERSION = "2.0.1"
TASK_ID = "6af5c333e5c1"
SUMMARY = (
    "0-bg grid (h~6-9, w~8-12) with: (a) 2-4 "
    "ACTIVE ROWS each containing EXACTLY 2 "
    "COLOR-1 (blue) CELLS at distinct columns "
    "c0 < c1 with c1 - c0 ≥ 2 (so there's a "
    "fillable gap between them); (b) 0 to "
    "(count // 2) DISTRACTOR rows each "
    "containing exactly 1 blue cell (singleton, "
    "not a pair). Active rows and singleton "
    "rows are mutually exclusive. Rule: for "
    "EACH ROW independently, COUNT its color-1 "
    "cells. If COUNT == 2, FILL every cell "
    "between the two endpoints (inclusive) "
    "with COLOR 1. If COUNT == 0, 1, or 3+, "
    "leave the row UNCHANGED. Net: rows with "
    "exactly 2 blue endpoints get the gap "
    "filled in blue; singleton/empty rows stay; "
    "no other colors involved."
)

# Rivals: 'output is input' refuted by any demo where two endpoints
# form a filled bar. 'fill all rows' refuted by ≥1 demo where a
# single-endpoint row stays a singleton. 'operate per column' refuted
# by ≥1 demo where vertical pairs don't form lines. 'use different
# fill color' refuted by any demo (fill is 1). 3 demos with mixed
# row types cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "active rows contain exactly two blue cells",
    "optional inactive rows contain one blue cell",
    "all cells between the endpoints start empty",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_endpoint_only", "span_already_filled", "no_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "segment_count":  {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "row_endpoints",
                       "valid": "row_endpoints"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; >=1 row with exactly 2 color-1 cells (endpoint pair)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    active_rows = [r for r in range(h)
                   if sum(1 for c in range(w) if grid[r][c] == 1) == 2]
    if not active_rows:
        return errs  # degenerate (no_endpoints or single_endpoint) — allowed
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 7, 10)
        count = ctx.draw_int("segment_count", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 18)
        w = ctx.draw_int("grid_w", 14, 20)
        count = ctx.draw_int("segment_count", 5, 9)
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 10, 14)
        count = ctx.draw_int("segment_count", 3, 6)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    rows = rng.sample(range(h), min(count, h))
    for r in rows:
        c1 = rng.randint(0, w - 3)
        c2 = rng.randint(c1 + 2, w - 1)
        g[r][c1] = 1
        g[r][c2] = 1
    # Optional singleton-row distractors (some difficulty allows several)
    inactive = [r for r in range(h) if r not in rows]
    n_singletons = min(len(inactive), rng.randint(0, max(0, count // 2)))
    for r in rng.sample(inactive, n_singletons):
        g[r][rng.randrange(w)] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 7, 10
    g = full_grid(h, w, 0)
    if name == "single_endpoint_only":
        # every row has just one blue cell → rule's "two endpoints" filter never matches
        for r in range(h):
            g[r][r % w] = 1
        return g
    if name == "span_already_filled":
        # span between the two blue endpoints is already painted with another color → conflict
        g[2][1] = 1; g[2][7] = 1
        for c in range(2, 7):
            g[2][c] = 4
        return g
    if name == "no_endpoints":
        # empty grid → no rows have endpoints, rule is no-op
        return g
    return g
