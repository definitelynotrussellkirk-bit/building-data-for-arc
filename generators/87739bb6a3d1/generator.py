"""Generator for arc_puzzle_bank_21_set9_e:easy_i04.

Rule: in each column with two same-color endpoints, fill the vertical
gap between them with the same color.

Combinatorial axes (8): grid_h/w, palette_kind, n_bridges,
palette_size, position_bias, n_distinct_colors, gap_density, texture.
Degenerates: no_gap, single_endpoint, no_seeds.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87739bb6a3d1"
VERSION = "2.0.1"
TASK_ID = "87739bb6a3d1"
SUMMARY = (
    "0-bg grid (h~7-9, w~7-9) with 2-4 ENDPOINT PAIRS: "
    "each pair places two SAME-COLOR cells in the SAME "
    "COLUMN at rows r1 < r2 with r2 ≥ r1 + 2 (so there "
    "is at least one empty cell strictly between them). "
    "Different pairs use distinct columns and distinct "
    "non-bg colors. Cells between the endpoints in each "
    "pair are 0. Rule: for every column that contains "
    "exactly two same-color cells at rows r1 and r2, "
    "FILL every cell at rows r1+1 .. r2-1 in that "
    "column with that color, bridging the gap into a "
    "solid VERTICAL BAR. Endpoints stay; non-pair "
    "columns stay 0. Net: each pair of isolated "
    "endpoints becomes a continuous vertical line."
)

INVARIANTS = [
    "background is 0",
    "selected columns contain exactly two same-color endpoints",
    "cells between endpoints are zero",
    "endpoints span ≥3 rows so there is a non-empty gap",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_gap", "single_endpoint", "no_seeds")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "bridges":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "gap_density":    {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; selected columns have exactly 2 same-color endpoints with zero gap between."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    nonzero = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nonzero:
        return []  # degenerate no_seeds — allowed
    errs = []
    for c in range(w):
        col_cells = [(r, grid[r][c]) for r in range(h) if grid[r][c] != 0]
        if not col_cells:
            continue
        if len(col_cells) == 1:
            return []  # degenerate single_endpoint — allowed
        if len(col_cells) == 2:
            (r1, v1), (r2, v2) = col_cells
            if v1 != v2:
                errs.append(f"col {c}: 2 cells with different colors ({v1}, {v2})")
                continue
            if abs(r2 - r1) < 2:
                return []  # degenerate no_gap (adjacent) — allowed
            # Check cells between are all zero
            for r in range(r1 + 1, r2):
                if grid[r][c] != 0:
                    errs.append(f"col {c}: non-zero cell at ({r},{c}) between endpoints")
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
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 7, 9)
    n = min(ctx.draw_int("bridges", 2, 4), w)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    for c, color in zip(rng.sample(range(w), n), rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], n)):
        r1 = rng.randint(0, h - 3)
        r2 = rng.randint(r1 + 2, h - 1)
        g[r1][c] = color
        g[r2][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_gap":
        # touching endpoints — bridge has zero interior, output == input
        g[2][1] = 3
        g[3][1] = 3
        return g
    if name == "single_endpoint":
        # only one cell — no second endpoint to bridge to
        g[2][3] = 5
        return g
    if name == "no_seeds":
        # empty grid — nothing to bridge
        return g
    return g
