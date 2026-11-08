"""Generator for arc_puzzle_bank_nineteenth21:E129.

Rule: sparse square grids whose cells are copied across the main diagonal.

Combinatorial axes (8): grid_h/w, grid_size, cells, palette_kind,
anchor_corner, asymmetry_force, palette_size, position_bias.
Degenerates: empty_grid, single_cell, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2d5d96f6a7b1"
VERSION = "1.1.0"
TASK_ID = "2d5d96f6a7b1"

SUMMARY = "Sparse square grids whose cells are copied across the main diagonal."

INVARIANTS = [
    "background is 0",
    "grid is square",
    "source cells are placed above the main diagonal",
    "each transposed target cell is initially empty",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("empty_grid", "single_cell", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "grid_w":         {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "grid_size":      {"type": "int", "default": "rng 5..8", "valid": "5..8"},
    "cells":          {"type": "int", "default": "rng 3..6", "valid": "3..6"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|empty_grid|single_cell|full_grid"},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        n = ctx.draw_int("grid_size", 5, 6)
    elif difficulty == "hard":
        n = ctx.draw_int("grid_size", 7, 8)
    else:
        n = ctx.draw_int("grid_size", 5, 8)
    target = ctx.draw_int("cells", 3, 6)
    g = full_grid(n, n, 0)
    candidates = [(r, c) for r in range(n) for c in range(r + 1, n)]
    rng.shuffle(candidates)
    for r, c in candidates[:target]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(6, 6, 0)
    if name == "empty_grid":
        return g
    if name == "single_cell":
        g[1][3] = 3
        return g
    if name == "full_grid":
        for r in range(6):
            for c in range(6):
                g[r][c] = 3
        return g
    return g

def self_check(grid, *, difficulty=None, meta=None):
    errs = []
    h, w = len(grid), len(grid[0]) if grid else 0
    if h != w:
        errs.append("grid must be square")
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        errs.append("need at least one source cell above the diagonal")
    for r, c in cells:
        if r >= c:
            errs.append("source cells must be strictly above the main diagonal")
            break
        if grid[c][r] != 0:
            errs.append("transposed target cell must be empty in the input")
            break
    return errs
