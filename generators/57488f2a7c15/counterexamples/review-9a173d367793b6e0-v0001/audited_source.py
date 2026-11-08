"""Generator for arc_puzzle_bank_fifth_21_bundle:easy_31_complete_main_diagonal_symmetry.

Rule: sparse square grid whose colored cells are copied across the
main diagonal.

Combinatorial axes (8): side, palette_kind, n_cells, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, on_diagonal_only, already_symmetric.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "57488f2a7c15"
VERSION = "1.1.1"
TASK_ID = "57488f2a7c15"
SUMMARY = "Sparse square grid whose colored cells are copied across the main diagonal."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "there is at least one off-diagonal source cell",
    "the pattern is not already main-diagonal symmetric",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "on_diagonal_only", "already_symmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "side":           {"type": "int", "default": "rng 5..9", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 3..6", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "4", "valid": "4"},
    "position_bias":  {"type": "str", "default": "off_diagonal", "valid": "off_diagonal"},
    "n_distinct_colors": {"type": "int", "default": "4", "valid": "4"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
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
        n = ctx.draw_int("side", 5, 6)
        n_cells = ctx.draw_int("n_cells", 2, 4)
    elif difficulty == "hard":
        n = ctx.draw_int("side", 8, 9)
        n_cells = ctx.draw_int("n_cells", 5, 6)
    else:
        n = ctx.draw_int("side", 5, 9)
        n_cells = ctx.draw_int("n_cells", 3, 6)
    colors = ctx.draw_distinct_colors("colors", n=4, exclude={0})
    rng = ctx.draw_rng("cells")
    g = full_grid(n, n, 0)
    candidates = [(r, c) for r in range(n) for c in range(n) if r != c]
    rng.shuffle(candidates)
    for i, (r, c) in enumerate(candidates[:n_cells]):
        g[r][c] = colors[i % len(colors)]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: square grid, at least one off-diagonal colored cell, not already symmetric."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    if h != w:
        errs.append(f"grid is not square: {h}x{w}")
        return errs
    n = h
    off_diag = [(r, c) for r in range(n) for c in range(n) if r != c and grid[r][c] != 0]
    if not off_diag:
        errs.append("no off-diagonal source cells found")
        return errs
    # Check not already symmetric across main diagonal
    symmetric = all(grid[r][c] == grid[c][r] for r in range(n) for c in range(n))
    if symmetric:
        errs.append("grid is already main-diagonal symmetric (no rule needed)")
    return errs


def _draw_from_degenerate(name, rng):
    n = 7
    g = full_grid(n, n, 0)
    if name == "empty_grid":
        # nothing to mirror — input equals output
        return g
    if name == "on_diagonal_only":
        # all sources on main diagonal → reflection is identity, rule no-op
        for i in range(n):
            g[i][i] = ((i % 7) + 1)
        return g
    if name == "already_symmetric":
        # pattern is already main-diagonal symmetric → rule has no visible effect
        for r, c in [(1, 3), (3, 1), (2, 5), (5, 2)]:
            g[r][c] = 4
        return g
    return g
