"""Generator for arc_puzzle_bank_21_set3:S3_E3.

Rule: columns with exactly two magenta endpoints are filled
vertically between them.

Combinatorial axes (8): grid_h, grid_w, palette_kind, span_count,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: single_endpoint_only, span_already_filled, no_endpoints.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2359fcadf037"
VERSION = "1.3.0"  # add executable self_check coverage for magenta vertical-span inputs
TASK_ID = "2359fcadf037"
SUMMARY = "Columns with exactly two magenta cells are filled vertically between them."

INVARIANTS = [
    "background is 0",
    "active columns have exactly two magenta endpoints",
    "cells between each endpoint pair are empty",
    "optional inactive columns contain three magenta cells and are not filled",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("single_endpoint_only", "span_already_filled", "no_endpoints")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "grid_w":         {"type": "int", "default": "rng 8..11", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "span_count":     {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "col_endpoints",
                       "valid": "col_endpoints"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
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
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 8, 9)
        count = ctx.draw_int("span_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 16)
        w = ctx.draw_int("grid_w", 12, 16)
        count = ctx.draw_int("span_count", 4, 7)
    else:
        h = ctx.draw_int("grid_h", 9, 13)
        w = ctx.draw_int("grid_w", 9, 13)
        count = ctx.draw_int("span_count", 2, min(5, w - 1))
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cols = rng.sample(range(w), count + 1)
    for c in cols[:count]:
        r1 = rng.randint(0, h - 4)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = 6
        g[r2][c] = 6
    c = cols[-1]
    for r in sorted(rng.sample(range(h), 3)):
        g[r][c] = 6
    return g


def _draw_from_degenerate(name, rng):
    h, w = 9, 9
    g = full_grid(h, w, 0)
    if name == "single_endpoint_only":
        # every active column has just one magenta cell → no pair, rule no-op
        for c in [1, 4, 7]:
            g[3][c] = 6
        return g
    if name == "span_already_filled":
        # span between endpoints is already painted with another color → conflict
        g[0][3] = 6; g[h - 1][3] = 6
        for r in range(1, h - 1):
            g[r][3] = 4
        return g
    if name == "no_endpoints":
        # no magenta cells → nothing to fill
        for r, c in [(2, 2), (5, 6)]:
            g[r][c] = 5
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    h, w = len(grid), len(grid[0])
    active = 0
    blocker = 0
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 6]
        if len(rows) == 2:
            active += 1
            if rows[1] - rows[0] < 2:
                errs.append(f"column {c} endpoint pair needs a visible gap")
            if any(grid[r][c] != 0 for r in range(rows[0] + 1, rows[1])):
                errs.append(f"column {c} span should be empty before fill")
        elif len(rows) == 3:
            blocker += 1
        elif len(rows) not in (0, 2, 3):
            errs.append(f"column {c} has unsupported magenta count {len(rows)}")
    min_expected = 4 if difficulty == "hard" else 2
    if active < min_expected:
        errs.append(f"expected at least {min_expected} active magenta columns, got {active}")
    if blocker < 1:
        errs.append("expected one inactive 3-endpoint distractor column")
    return errs
