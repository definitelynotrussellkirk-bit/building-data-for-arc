"""Generator for arc_puzzle_bank_21_set15_bundle:easy_o05.

Rule: upper-triangular content is mirrored across the main diagonal
into the lower triangle.

Combinatorial axes (8): size, palette_kind, cell_count, palette_size,
position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, all_on_diagonal, full_lower_tri.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5875afa30211"
VERSION = "1.1.0"
TASK_ID = "5875afa30211"
SUMMARY = "Square grids with sparse content on and above the diagonal."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "colored cells are placed only on or above the main diagonal",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("empty_grid", "all_on_diagonal", "full_lower_tri")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "size":           {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "default|sparse|dense|varied_palette"},
    "cell_count":     {"type": "int", "default": "rng 6..12", "valid": "1..30"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "upper_tri",
                       "valid": "upper_tri"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "default|sparse|dense|varied_palette|empty_grid|all_on_diagonal|full_lower_tri"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("size", 6, 7)
    elif difficulty == "hard":
        n = ctx.draw_int("size", 8, 9)
    else:
        n = ctx.draw_int("size", 6, 9)
    cell_count = ctx.draw_int("cell_count", 6, min(12, n * (n + 1) // 2))
    colors = ctx.draw_distinct_colors("colors", n=5, exclude={0})
    rng = ctx.draw_rng("layout")

    g = full_grid(n, n, 0)
    positions = [(r, c) for r in range(n) for c in range(r, n)]
    rng.shuffle(positions)
    for i, (r, c) in enumerate(positions[:cell_count]):
        g[r][c] = colors[i % len(colors)]
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    n = len(grid)
    if len(grid[0]) != n:
        errors.append(f"grid must be square, found {n}x{len(grid[0])}")
    for r in range(n):
        for c in range(min(r, len(grid[0]))):
            if grid[r][c] != 0:
                errors.append(f"cell below diagonal at {(r, c)} is nonzero")
                return errors
    above = [(r, c) for r in range(n) for c in range(r + 1, len(grid[0])) if grid[r][c] != 0]
    if not above:
        errors.append("normal sample needs at least one above-diagonal cell so mirroring is nontrivial")
    return errors


def _draw_from_degenerate(name, rng):
    n = 7
    g = full_grid(n, n, 0)
    if name == "empty_grid":
        # nothing to mirror — output identical to input
        return g
    if name == "all_on_diagonal":
        # all cells exactly on diagonal — mirror is identity (rule trivial)
        for i in range(n):
            g[i][i] = (i % 5) + 2
        return g
    if name == "full_lower_tri":
        # lower triangle already filled — invariant violated
        for r in range(n):
            for c in range(r):
                g[r][c] = 6  # below diagonal
        g[1][3] = 4
        g[0][5] = 7
        return g
    return g
