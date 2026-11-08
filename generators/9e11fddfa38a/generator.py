"""Generator for arc_puzzle_bank_21_set24_bundle:easy_p02.

Rule: sparse cells echoed across the anti-diagonal.

Combinatorial axes (8): grid_n, palette_kind, cell_count, n_blobs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: cells_on_antidiag, cells_already_symmetric, empty_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "9e11fddfa38a"
VERSION = "1.1.1"
TASK_ID = "9e11fddfa38a"
SUMMARY = "Sparse square-grid cells are echoed across the anti-diagonal."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "no input cell occupies another input cell's anti-diagonal reflection",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("cells_on_antidiag", "cells_already_symmetric", "empty_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_n":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cell_count":     {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "palette_size":   {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "off_antidiag",
                       "valid": "off_antidiag"},
    "n_distinct_colors": {"type": "int", "default": "rng 3..5", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "n_blobs":        {"type": "int", "default": "1", "valid": "1..1"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid is square with bg=0; no cell and its anti-diagonal reflection are both nonzero."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    if h != w:
        errs.append(f"grid is not square: {h}×{w}")
        return errs
    n = h
    for r in range(n):
        for c in range(n):
            if grid[r][c] != 0:
                mr, mc = n - 1 - c, n - 1 - r
                if (mr, mc) != (r, c) and grid[mr][mc] != 0:
                    errs.append(
                        f"cell ({r},{c})={grid[r][c]} and its anti-diagonal "
                        f"reflection ({mr},{mc})={grid[mr][mc]} are both nonzero"
                    )
                    return errs  # report first violation only
    return errs


def _anti_reflect(n: int, r: int, c: int) -> tuple[int, int]:
    return n - 1 - c, n - 1 - r


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        n = ctx.draw_int("grid_n", 7, 7)
        cell_count = ctx.draw_int("cell_count", 3, 3)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_n", 9, 10)
        cell_count = ctx.draw_int("cell_count", 4, 5)
    else:
        n = ctx.draw_int("grid_n", 7, 10)
        cell_count = ctx.draw_int("cell_count", 3, 5)
    rng = ctx.draw_rng("layout")
    grid = full_grid(n, n, 0)
    positions = [(r, c) for r in range(n) for c in range(n)
                 if (r, c) != _anti_reflect(n, r, c)]
    rng.shuffle(positions)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], min(cell_count, 9))
    used: set[tuple[int, int]] = set()
    placed = 0

    for r, c in positions:
        mirror = _anti_reflect(n, r, c)
        if (r, c) in used or mirror in used:
            continue
        grid[r][c] = colors[placed % len(colors)]
        used.add((r, c))
        used.add(mirror)
        placed += 1
        if placed >= cell_count:
            break
    return grid


def _draw_from_degenerate(name, rng):
    n = 7
    g = full_grid(n, n, 0)
    if name == "cells_on_antidiag":
        # cells on anti-diagonal are their own mirrors → echo is identity for them
        for r, c, v in [(0, 6, 4), (3, 3, 5), (6, 0, 6)]:
            g[r][c] = v
        return g
    if name == "cells_already_symmetric":
        # cells and their anti-reflections both painted → output equals input, rule is identity
        pairs = [((1, 2), (4, 5)), ((0, 3), (3, 6)), ((2, 5), (1, 4))]
        for (r1, c1), (r2, c2) in pairs:
            g[r1][c1] = 4
            g[r2][c2] = 4
        return g
    if name == "empty_grid":
        # no cells → echo has nothing to do, rule no-op
        return g
    return g
