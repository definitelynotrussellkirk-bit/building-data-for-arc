"""Generator for arc_puzzle_bank_twentieth_21_bundle:easy_135_complete_main_diagonal_reflection.

Rule: nonzero cells are copied across the main diagonal.

Combinatorial axes (8): grid_n, palette_kind, cells, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, on_diagonal_only, already_symmetric.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "230b4cccda08"
VERSION = "1.1.1"
TASK_ID = "230b4cccda08"
SUMMARY = "Nonzero cells are copied across the main diagonal."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "source cells are sparse",
    "reflected destinations are initially blank unless the source is on the diagonal",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "on_diagonal_only", "already_symmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_n":         {"type": "int", "default": "rng 7..11", "valid": "3..20"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells":          {"type": "int", "default": "rng 5..10", "valid": "1..40"},
    "palette_size":   {"type": "int", "default": "rng 1..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "above_diagonal", "valid": "above_diagonal"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: grid is square; any non-zero cell is on or above the main diagonal (never strictly below)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    if h != w:
        errors.append(f"grid not square: {h}×{w}")
        return errors
    # Cells strictly below diagonal (r > c) must be 0 in normal inputs
    below_diag = [grid[r][c] for r in range(h) for c in range(r) if grid[r][c] != 0]
    if below_diag:
        errors.append(f"non-zero cells strictly below diagonal: {below_diag[:3]}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 7, 8)
        count = ctx.draw_int("cells", 4, 6)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 10, 11)
        count = ctx.draw_int("cells", 8, 10)
    else:
        n = ctx.draw_int("grid_n", 7, 11)
        count = ctx.draw_int("cells", 5, 10)
    rng = ctx.draw_rng("layout")
    g = full_grid(n, n, 0)
    choices = [(r, c) for r in range(n) for c in range(r + 1, n)]
    rng.shuffle(choices)
    for r, c in choices[:min(count, len(choices))]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    if count > 6:
        d = rng.randrange(n)
        g[d][d] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    n = 8
    g = full_grid(n, n, 0)
    if name == "empty_grid":
        # no cells to mirror — input equals output
        return g
    if name == "on_diagonal_only":
        # all sources on main diagonal → reflection is identity, rule no-op
        for i in range(n):
            g[i][i] = ((i % 7) + 1)
        return g
    if name == "already_symmetric":
        # pattern is already main-diagonal symmetric → rule has no visible effect
        for r, c in [(1, 4), (4, 1), (2, 6), (6, 2), (3, 5), (5, 3)]:
            g[r][c] = 4
        return g
    return g
