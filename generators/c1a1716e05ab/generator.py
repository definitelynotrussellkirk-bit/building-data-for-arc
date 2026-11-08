"""Generator for arc_puzzle_bank_seventeenth_21_bundle:easy_113_complete_horizontal_mirror.

Rule: sparse upper-half cells are copied across the horizontal axis.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: empty_grid, lower_half_only, already_symmetric.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c1a1716e05ab"
VERSION = "1.1.1"
TASK_ID = "c1a1716e05ab"
SUMMARY = "Sparse upper-half cells are copied across the horizontal axis."

INVARIANTS = [
    "background is 0",
    "source cells are off the horizontal mirror axis",
    "mirrored target cells are initially empty",
    "colors are preserved by the mirror copy",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_grid", "lower_half_only", "already_symmetric")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..18"},
    "grid_w":         {"type": "int", "default": "rng 7..11", "valid": "4..18"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cells":          {"type": "int", "default": "rng 3..7", "valid": "1..24"},
    "palette_size":   {"type": "int", "default": "rng 1..9", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "upper_half", "valid": "upper_half"},
    "n_distinct_colors": {"type": "int", "default": "rng 1..9", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; all non-zero cells are in the upper half (rows < h//2)."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    half = h // 2
    lower_nonzero = [(r, c) for r in range(half, h) for c in range(w) if grid[r][c] != 0]
    upper_nonzero = [(r, c) for r in range(half) for c in range(w) if grid[r][c] != 0]
    if not upper_nonzero:
        errs.append("no non-zero cells found in upper half")
    if lower_nonzero:
        errs.append(f"{len(lower_nonzero)} non-zero cell(s) in lower half (should be empty)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("cells", 3, 4)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 10, 11)
        target = ctx.draw_int("cells", 5, 7)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 7, 11)
        target = ctx.draw_int("cells", 3, 7)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    candidates = [(r, c) for r in range(h // 2) for c in range(w)]
    rng.shuffle(candidates)
    for r, c in candidates[:target]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8, 9])
    return g



def self_check(grid, *, difficulty=None, meta=None):
    """Executable invariants for horizontal mirror-copy inputs."""
    errs = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    cells = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not cells:
        return ["expected at least one source cell in the upper half"]
    for r, c in cells:
        if r >= h // 2:
            errs.append(f"source cell {(r, c)} is not strictly in the upper half")
            break
        mr = h - 1 - r
        if mr == r:
            errs.append(f"source cell {(r, c)} lies on mirror axis")
            break
        if grid[mr][c] != 0:
            errs.append(f"mirror target {(mr, c)} is not initially empty")
            break
    return errs


def _draw_from_degenerate(name, rng):
    h, w = 8, 9
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        # no cells to mirror — input equals output
        return g
    if name == "lower_half_only":
        # all sources in the lower half → upper-half-source assumption violated
        for r, c in [(5, 1), (6, 3), (5, 6), (7, 4)]:
            g[r][c] = 3
        return g
    if name == "already_symmetric":
        # pattern is already horizontal-mirror symmetric → rule has no visible effect
        for r, c in [(1, 2), (h - 1 - 1, 2), (2, 5), (h - 1 - 2, 5)]:
            g[r][c] = 4
        return g
    return g
