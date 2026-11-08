"""Generator for arc_puzzle_bank_21_set17_s:S17_E1.

Rule: sparse seeds grow by the plus stencil.

Combinatorial axes (8): grid_h/w, seed_count, palette_kind, anchor_corner,
asymmetry_force, palette_size, position_bias, n_distinct_colors.
Degenerates: no_seeds, full_seeds, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "bf47583ab6e3"
VERSION = "2.1.0"  # out_shapes 9: grid 6..8 fixed. Output=same dims (seed->plus); widen grid (5..13 normal) + more seeds.
TASK_ID = "bf47583ab6e3"
SUMMARY = (
    "0-bg grid (h~6-8, w~6-8) with 2-4 SPARSE SEED "
    "cells placed at random positions, each in a "
    "distinct non-bg color (the seed colors are simply "
    "2, 3, 4, 5 in placement order). Rule: for each "
    "non-bg seed cell at (r, c), STAMP a 5-cell PLUS "
    "shape in color 8 (cyan): the center (r, c) and "
    "the four cardinal neighbors (r-1, c), (r+1, c), "
    "(r, c-1), (r, c+1). Cells that fall outside the "
    "grid are clipped. The seed cells themselves are "
    "OVERPAINTED to color 8 (their original color is "
    "replaced). Net: every colored seed dot becomes a "
    "cyan plus-sign on a black field; the original "
    "seed colors disappear."
)

INVARIANTS = [
    "input contains two to four nonzero seed cells",
    "seed cells may use arbitrary non-background colors",
    "output is the union of plus-shaped stencils around the seeds",
]

PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DEGENERATE_TEXTURES = ("no_seeds", "full_seeds", "full_grid")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "height":         {"type": "int", "default": "rng 6..8", "valid": "3..14"},
    "width":          {"type": "int", "default": "rng 6..8", "valid": "3..14"},
    "seed_count":     {"type": "int", "default": "rng 2..4", "valid": "1..10"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "anchor_corner":  {"type": "bool", "default": "false",
                       "valid": "true|false"},
    "asymmetry_force":{"type": "bool", "default": "false",
                       "valid": "true|false"},
    "palette_size":   {"type": "int", "default": "varied", "valid": "varied"},
    "position_bias":  {"type": "str", "default": "random", "valid": "random"},
    "n_distinct_colors":{"type": "int", "default": "varied", "valid": "varied"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("height", 4, 7)
        w = ctx.draw_int("width", 4, 7)
        n = ctx.draw_int("seed_count", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("height", 10, 14)
        w = ctx.draw_int("width", 10, 14)
        n = ctx.draw_int("seed_count", 4, 6)
    else:
        h = ctx.draw_int("height", 5, 13)
        w = ctx.draw_int("width", 5, 13)
        n = ctx.draw_int("seed_count", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    cells = [(r, c) for r in range(h) for c in range(w)]
    for idx, (r, c) in enumerate(rng.sample(cells, n)):
        g[r][c] = 2 + idx
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for the seed-to-plus-stencil normal samples."""
    errors: list[str] = []
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    if difficulty == "easy":
        h_range, w_range, n_range = (4, 7), (4, 7), (2, 3)
    elif difficulty == "hard":
        h_range, w_range, n_range = (10, 14), (10, 14), (4, 6)
    else:
        h_range, w_range, n_range = (5, 13), (5, 13), (2, 4)
    if not (h_range[0] <= h <= h_range[1] and w_range[0] <= w <= w_range[1]):
        errors.append(f"grid size {h}x{w} outside expected range for difficulty={difficulty}")
    seeds = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v != 0]
    if not (n_range[0] <= len(seeds) <= n_range[1]):
        errors.append(f"seed count {len(seeds)} outside expected range {n_range} for difficulty={difficulty}")
        return errors
    colors = sorted(v for _, _, v in seeds)
    expected = list(range(2, 2 + len(seeds)))
    if colors != expected:
        errors.append(f"normal seed colors should be consecutive {expected}, found {colors}")
    if 8 in colors:
        errors.append("input seeds must not use reserved output color 8")
    return errors


def _draw_from_degenerate(name, rng):
    g = full_grid(7, 7, 0)
    if name == "no_seeds":
        return g
    if name == "full_seeds":
        for r in range(7):
            for c in range(7):
                if (r + c) % 2 == 0:
                    g[r][c] = 2
        return g
    if name == "full_grid":
        for r in range(7):
            for c in range(7):
                g[r][c] = 2
        return g
    return g
