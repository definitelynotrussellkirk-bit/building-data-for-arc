"""Generator for arc_additional_puzzles_21_set3:E20.

Rule: for each (r, c) where g[r][c] = 4 and g[r][c+1] = 4, set
g[r][c-1] = 9 and g[r][c+2] = 9 (if in-bounds and currently 0).

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: pair_at_edge, single_4_only, no_pairs.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a0abd95c485b"
VERSION = "2.0.1"
TASK_ID = "a0abd95c485b"
SUMMARY = (
    "0-bg grid (h~5-7, w~8-10) with "
    "2-3 HORIZONTAL COLOR-4 (yellow) "
    "PAIRS — each pair is 2 adjacent "
    "color-4 cells at (r, c) and "
    "(r, c+1) where 1 ≤ c ≤ w-3 (so "
    "both flanking cells c-1 and c+2 "
    "are in-bounds and remain 0). "
    "Each pair occupies a DISTINCT "
    "ROW (no two pairs share a row). "
    "Rule (FLANK WITH 9s): for EVERY "
    "(r, c) where g[r][c]==4 AND "
    "g[r][c+1]==4, set g[r][c-1] = 9 "
    "(maroon) AND g[r][c+2] = 9 — but "
    "only if both target cells are "
    "in-bounds AND currently 0. The "
    "color-4 pair stays. Net: each "
    "horizontal yellow domino gets "
    "flanked left+right by maroon "
    "cells."
)

INVARIANTS = [
    "≥2 horizontal (4,4) pairs in distinct rows",
    "left and right of each pair is in-bounds and 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("pair_at_edge", "single_4_only", "no_pairs")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..7", "valid": "4..10"},
    "grid_w":         {"type": "int", "default": "rng 8..10", "valid": "6..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_pairs":        {"type": "int", "default": "rng 2..3", "valid": "1..5"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1"},
    "position_bias":  {"type": "str", "default": "row_local", "valid": "row_local"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """bg=0; >=2 rows each with a horizontal (4,4) domino and flanking zeros in-bounds."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    valid_pairs = 0
    for r in range(h):
        for c in range(1, w - 2):  # c-1 and c+2 must be in-bounds
            if grid[r][c] == 4 and grid[r][c + 1] == 4:
                if grid[r][c - 1] == 0 and grid[r][c + 2] == 0:
                    valid_pairs += 1
                    break
    if valid_pairs < 2:
        errs.append(f"fewer than 2 valid (4,4) pairs with flanking zeros: found {valid_pairs}")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 6)
        w = ctx.draw_int("grid_w", 8, 9)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 5, 7)
        w = ctx.draw_int("grid_w", 8, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    used_rows = set()
    for _ in range(rng.randint(2, 3)):
        for _ in range(20):
            r = rng.randint(0, h - 1)
            if r in used_rows:
                continue
            c = rng.randint(1, w - 3)
            g[r][c] = 4; g[r][c + 1] = 4
            used_rows.add(r)
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 6, 9
    g = full_grid(h, w, 0)
    if name == "pair_at_edge":
        # pair at col 0..1 or w-2..w-1 → flank cell is out-of-bounds, partial decoration
        g[1][0] = 4; g[1][1] = 4
        g[3][w - 2] = 4; g[3][w - 1] = 4
        return g
    if name == "single_4_only":
        # 4 cells exist but never as horizontal adjacent pair → no rule trigger
        for r, c in [(1, 2), (3, 5), (5, 7)]:
            g[r][c] = 4
        return g
    if name == "no_pairs":
        # empty grid → no 4-pairs, no flanking
        return g
    return g
