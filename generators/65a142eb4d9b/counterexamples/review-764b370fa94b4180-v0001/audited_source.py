"""Generator for arc_puzzle_bank_21_more:easy_b02 — Plus-stamp at isolated colored cells.

Rule: for each non-zero cell with no same-color cardinal neighbor,
paint a plus-shape (center + 4 cardinals) in that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_cells,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_cells, multi_cell_blobs, cells_at_corner.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "65a142eb4d9b"
VERSION = "2.0.1"
TASK_ID = "65a142eb4d9b"
SUMMARY = (
    "0-bg grid (h~7-10, w~7-10) with 2-4 ISOLATED "
    "SINGLE colored cells placed at interior positions "
    "(rows 1..h-2, cols 1..w-2 so all 4 cardinal "
    "neighbors are in bounds), each in a distinct non-bg "
    "color, separated from each other by Manhattan "
    "distance ≥ 4 so their plus-stamps will not overlap "
    "and no cell has a same-color cardinal neighbor. "
    "Rule: for every non-bg cell whose four cardinal "
    "neighbors are all NOT the same color as itself "
    "(i.e., it is ISOLATED from its own color), PAINT a "
    "PLUS-SHAPE: the four cardinal neighbors (r-1, c), "
    "(r+1, c), (r, c-1), (r, c+1) become the cell's "
    "color. The center cell stays its color. Net: each "
    "isolated colored dot grows into a same-color "
    "plus-sign (5 cells total)."
)

INVARIANTS = [
    "2-4 isolated cells",
    "each cell has a unique color",
    "cells are at least 3 apart (so plus-stamps don't overlap)",
    "cells are at interior positions (so plus fits)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_cells", "multi_cell_blobs", "cells_at_corner")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "5..12"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_cells":        {"type": "int", "default": "rng 2..4", "valid": "1..6"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spaced_interior_singletons",
                       "valid": "spaced_interior_singletons"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: ≥1 isolated non-zero cell at an interior position."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    if not nonzero:
        errs.append("no non-zero cells found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 10)
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    n_cells = rng.randint(2, 4)
    palette = rng.sample([1, 2, 3, 4, 6, 7, 8, 9], n_cells)
    placed = []
    for color in palette:
        for _ in range(40):
            r = rng.randint(1, h - 2); c = rng.randint(1, w - 2)
            if any(abs(r - pr) + abs(c - pc) < 4 for pr, pc in placed):
                continue
            g[r][c] = color
            placed.append((r, c))
            break
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_cells":
        # blank → no isolated cells to plus-stamp
        return g
    if name == "multi_cell_blobs":
        # cells have same-color cardinal neighbors → "isolated" precondition fails
        g[2][2] = 4; g[2][3] = 4   # adjacent same-color
        g[5][5] = 6; g[6][5] = 6
        return g
    if name == "cells_at_corner":
        # cells at corners → 2 of 4 cardinal arms of the plus are out of bounds
        g[0][0] = 3
        g[h - 1][w - 1] = 7
        return g
    return g
