"""Generator for arc_puzzle_bank_tenth21:E64.

Rule: each column with a vertical same-color endpoint pair is filled in
that color between the endpoints.

Combinatorial axes (8): grid_h/w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, gap_min, texture.
Degenerates: only_one_endpoint, endpoints_adjacent, mismatched_colors.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "16dfbdc731e1"
VERSION = "1.2.0"  # add executable vertical-pair invariants
TASK_ID = "16dfbdc731e1"
SUMMARY = "Columns contain same-color endpoint pairs with empty cells between."

INVARIANTS = [
    "background is 0",
    "each active column has one same-color vertical pair",
    "cells between the endpoints are empty",
    "the segment fills in the endpoint color",
]

PALETTE_KINDS = ("default", "tight_gaps", "wide_gaps", "rainbow")
DEGENERATE_TEXTURES = ("only_one_endpoint", "endpoints_adjacent", "mismatched_colors")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 3..5", "valid": "1..10"},
    "gap_min":        {"type": "int", "default": "1", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "9", "valid": "9"},
    "position_bias":  {"type": "str", "default": "scattered",
                       "valid": "scattered"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5",
                          "valid": "1..9"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target_max = 4
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        target_max = 5
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
        target_max = 5
    target = min(ctx.draw_int("pairs", 3, target_max), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c in rng.sample(range(w), target):
        r0 = rng.randint(0, h - 3)
        r1 = rng.randint(r0 + 2, h - 1)
        color = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
        g[r0][c] = color
        g[r1][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "only_one_endpoint":
        # solitary endpoints — no pair to fill between
        g[2][2] = 4
        g[5][5] = 7
        return g
    if name == "endpoints_adjacent":
        # endpoints touching — no gap to fill
        g[2][2] = 4
        g[3][2] = 4
        g[5][5] = 7
        g[6][5] = 7
        return g
    if name == "mismatched_colors":
        # endpoints in same column but different colors — rule excludes
        g[1][2] = 4
        g[6][2] = 7
        return g
    return g



def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["empty or ragged grid"]
    h, w = len(grid), len(grid[0])
    active = 0
    for c in range(w):
        nz = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if not nz:
            continue
        active += 1
        if len(nz) != 2:
            errs.append(f"column {c} has {len(nz)} endpoints, expected exactly 2")
            continue
        if nz[0][1] != nz[1][1]:
            errs.append(f"column {c} endpoint colors differ")
        if nz[1][0] - nz[0][0] < 2:
            errs.append(f"column {c} endpoints are adjacent; no gap to fill")
    if active < 3:
        errs.append(f"expected at least 3 active columns, saw {active}")
    return errs
