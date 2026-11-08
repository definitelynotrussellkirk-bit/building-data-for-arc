"""Generator for arc_puzzle_bank_21_set22_bundle:easy_p06.

Rule: nonzero top-row seeds project downward until optional 9 blockers.

Combinatorial axes (8): grid_h, grid_w, palette_kind, seed_count,
palette_size, position_bias, n_distinct_colors, blocker_density, texture.
Degenerates: no_seeds, all_blocked, blocker_in_row_zero.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1198580cc354"
VERSION = "1.1.1"  # +self_check
TASK_ID = "1198580cc354"
SUMMARY = "Nonzero top-row seeds project downward until optional 9 blockers."

INVARIANTS = [
    "background is 0",
    "all beam seeds are in row 0 and are not 9",
    "blockers use color 9 below some seed columns",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_seeds", "all_blocked", "blocker_in_row_zero")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "row_zero", "valid": "row_zero"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "blocker_density": {"type": "str", "default": "mixed", "valid": "mixed"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 9)
        seed_count = min(ctx.draw_int("seed_count", 2, 3), w)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        seed_count = min(ctx.draw_int("seed_count", 3, 4), w)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        seed_count = min(ctx.draw_int("seed_count", 2, 4), w)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    cols = rng.sample(range(w), seed_count)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], seed_count)
    for c, color in zip(cols, colors):
        grid[0][c] = color
        if h >= 5 and rng.random() < 0.55:
            grid[rng.randint(2, h - 1)][c] = 9
    return grid


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row 0 has at least one non-zero, non-9 seed cell (the beam source)."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    w = len(grid[0])
    errors = []
    seeds = [grid[0][c] for c in range(w) if grid[0][c] not in (0, 9)]
    if not seeds:
        errors.append("row 0 has no non-{0,9} seed cells — no beams to project")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_seeds":
        # row 0 empty; rule has no source → output is empty
        return g
    if name == "all_blocked":
        # every seed has its blocker on row 1 → every beam length is 0
        for c, color in [(2, 4), (5, 6), (7, 3)]:
            g[0][c] = color
            g[1][c] = 9
        return g
    if name == "blocker_in_row_zero":
        # 9 in row 0 along with seeds → ambiguous: is 9 a seed or a blocker?
        g[0][2] = 4
        g[0][5] = 9
        g[0][7] = 6
        return g
    return g
