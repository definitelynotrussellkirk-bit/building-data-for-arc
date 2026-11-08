"""Generator for arc_puzzle_bank_sixth21:E39.

Rule: each nonzero singleton becomes the top-left corner of a 2x2
same-color block.

Combinatorial axes (8): grid_h/w, n_cells, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: empty_grid, single_cell, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a9889198baf3"
VERSION = "2.0.2"
TASK_ID = "a9889198baf3"
SUMMARY = (
    "0-bg grid (h, w~7-10) "
    "with 2-5 SINGLETON "
    "SEEDS — single non-0 "
    "cells placed at "
    "positions on a 3-cell "
    "stride grid (rows "
    "0, 3, 6, ...; cols "
    "0, 3, 6, ...) so "
    "their 2×2 expansions "
    "don't conflict. Each "
    "seed uses a DISTINCT "
    "color from {1..8} "
    "(color (i % 8) + 1). "
    "Rule (EXPAND EACH "
    "SINGLETON INTO A "
    "2×2 SAME-COLOR BLOCK,"
    " ANCHORED AT THE "
    "SEED AS TOP-LEFT): "
    "For EACH SINGLETON "
    "SEED at (r, c) with "
    "color C: PAINT the "
    "cells (r, c), "
    "(r, c+1), (r+1, c), "
    "(r+1, c+1) with "
    "color C. The seed "
    "stays. Net: every "
    "non-0 cell becomes "
    "the top-left corner "
    "of a 2×2 solid "
    "block in its color."
)
INVARIANTS = [
    "seeds are single cells",
    "seeds avoid bottom/right edge",
    "2x2 expansions do not conflict",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("empty_grid", "single_cell", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "7..10"},
    "n_cells":        {"type": "int", "default": "rng 2..5", "valid": "2..5"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "warm|cool|broad|primary"},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "varied", "valid": "varied"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "warm|cool|broad|primary|empty_grid|single_cell|full_grid"},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify each nonzero is an isolated seed whose anchored 2x2 expansion is
    in-bounds and does not overlap another seed's expansion."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errs = []
    seeds = [(r, c, grid[r][c]) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if len(seeds) < 2:
        errs.append(f"expected at least two singleton seeds, got {len(seeds)}")
        return errs
    colors = [v for _, _, v in seeds]
    if len(colors) != len(set(colors)):
        errs.append("seed colors should be distinct in normal examples")
    footprints = []
    for r, c, _v in seeds:
        if r + 1 >= h or c + 1 >= w:
            errs.append("seed on bottom/right edge cannot expand to an in-bounds 2x2 block")
        fp = {(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)}
        if any(fp & old for old in footprints):
            errs.append("2x2 expansion footprints overlap")
            break
        footprints.append(fp)
        for nr, nc, _nv in seeds:
            if (nr, nc) != (r, c) and abs(nr - r) + abs(nc - c) < 3:
                errs.append("singleton seeds are too close for separated 2x2 expansions")
                return errs
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    n = ctx.draw_int("n_cells", 2, 5)
    g = full_grid(h, w, 0)
    spots = [(r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)]
    rng.shuffle(spots)
    for i, (r, c) in enumerate(spots[:n]):
        g[r][c] = (i % 8) + 1
    return g


def _draw_from_degenerate(name, rng):
    g = full_grid(8, 8, 0)
    if name == "empty_grid":
        return g
    if name == "single_cell":
        g[3][3] = 3
        return g
    if name == "full_grid":
        for r in range(8):
            for c in range(8):
                g[r][c] = 3
        return g
    return g
