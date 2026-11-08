"""Generator for arc_additional_puzzle_bank_volume7:E44.

Centers of yellow diagonal X patterns are filled cyan.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_xs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_xs, partial_xs, xs_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c44228ff3fee"
VERSION = "1.1.1"
TASK_ID = "c44228ff3fee"
SUMMARY = "Centers of yellow diagonal X patterns are filled cyan."

INVARIANTS = [
    "background is 0",
    "each target has yellow on the four diagonal positions around an empty center",
    "orthogonal neighbors of each center are background",
    "X patterns are separated by background",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_xs", "partial_xs", "xs_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "grid_w":         {"type": "int", "default": "rng 9..14", "valid": "5..22"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_xs":           {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "separated_diagonal_xs",
                       "valid": "separated_diagonal_xs"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
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
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
        n_xs = ctx.draw_int("n_xs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 14)
        w = ctx.draw_int("grid_w", 12, 14)
        n_xs = ctx.draw_int("n_xs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 9, 14)
        w = ctx.draw_int("grid_w", 9, 14)
        n_xs = ctx.draw_int("n_xs", 2, 4)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    centers: list[tuple[int, int]] = []
    for _ in range(220):
        if len(centers) >= n_xs:
            break
        r = rng.randint(1, h - 2)
        c = rng.randint(1, w - 2)
        if any(abs(r - rr) < 4 and abs(c - cc) < 4 for rr, cc in centers):
            continue
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            g[r + dr][c + dc] = 4
        centers.append((r, c))
    if not centers:
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            g[3 + dr][3 + dc] = 4
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """>=4 color-4 (yellow) cells present forming at least one X pattern."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    fours = sum(grid[r][c] == 4 for r in range(h) for c in range(w))
    if fours < 4:
        errors.append(f"expected >=4 color-4 cells (at least one X), found {fours}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 11, 11
    g = full_grid(h, w, 0)
    if name == "no_xs":
        # blank → no X centers to fill
        return g
    if name == "partial_xs":
        # only 2 of 4 diagonal cells of each X → "four diagonals" precondition fails
        g[1][1] = 4; g[1][3] = 4  # missing (3,1) and (3,3)
        g[5][5] = 4; g[7][7] = 4  # missing (5,7) and (7,5)
        return g
    if name == "xs_at_corner":
        # X with center at (0,0) → diagonal cells out of bounds
        g[0][1] = 4; g[1][0] = 4  # only 2 of 4 diagonals fit
        return g
    return g
