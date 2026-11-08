"""Generator for arc_puzzle_bank_fourteenth21:E92 — connect vertical endpoint pairs.

Rule: each column with 2 same-color cells gets the column span between
them filled with that color.

Combinatorial axes (8): grid_h, grid_w, palette_kind, pairs,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_pairs, mismatched_endpoints, span_already_filled.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "305d0c16596e"
VERSION = "2.0.1"
TASK_ID = "305d0c16596e"
SUMMARY = (
    "0-bg grid (h~7-10, w~7-9) containing 2-4 ENDPOINT "
    "PAIRS: each pair is two cells of the SAME UNIQUE "
    "COLOR in the SAME COLUMN, with at least one empty "
    "(0) cell between them. Different pairs use different "
    "colors and different columns. Rule: for each column "
    "containing exactly two same-color cells at rows r1 < "
    "r2, FILL every cell at rows r1..r2 in that column "
    "with that color (CONNECT the two endpoints into a "
    "solid vertical bar). Other cells are unchanged. Net: "
    "each pair of isolated endpoints becomes a continuous "
    "colored line spanning its column."
)

INVARIANTS = [
    "background is 0",
    "each active color appears exactly twice",
    "same-color endpoints share a column",
    "cells between endpoints are initially zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_pairs", "mismatched_endpoints", "span_already_filled")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "4..16"},
    "grid_w":         {"type": "int", "default": "rng 7..9", "valid": "4..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "pairs":          {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "position_bias":  {"type": "str", "default": "col_endpoint_pairs",
                       "valid": "col_endpoint_pairs"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Each non-zero color appears exactly twice, sharing the same column."""
    if not grid or not grid[0]:
        return ["empty grid"]
    if any(len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    h, w = len(grid), len(grid[0])
    errs = []
    # Group non-zero cells by color
    by_color = {}
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
            if v != 0:
                by_color.setdefault(v, []).append((r, c))
    if not by_color:
        errs.append("no non-zero cells found")
        return errs
    for color, cells in by_color.items():
        if len(cells) != 2:
            errs.append(f"color {color} appears {len(cells)} times (expect exactly 2)")
        elif cells[0][1] != cells[1][1]:
            errs.append(f"color {color} endpoints in different columns ({cells[0][1]} vs {cells[1][1]})")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 7, 8)
        target = ctx.draw_int("pairs", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 8, 9)
        target = ctx.draw_int("pairs", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 7, 9)
        target = ctx.draw_int("pairs", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], k=target)
    used_cols: set[int] = set()
    placed = 0
    for _ in range(200):
        if placed >= target:
            break
        c = rng.randrange(w)
        if c in used_cols:
            continue
        r1 = rng.randint(0, h - 3)
        r2 = rng.randint(r1 + 2, h - 1)
        color = colors[placed]
        g[r1][c] = color
        g[r2][c] = color
        used_cols.add(c)
        placed += 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_pairs":
        # singletons only → no pair to connect
        g[1][2] = 4
        g[3][5] = 6
        return g
    if name == "mismatched_endpoints":
        # endpoints with different colors → "same-color pair" precondition fails
        g[1][2] = 4; g[5][2] = 6   # mismatched in same col
        g[2][5] = 3; g[6][5] = 7   # mismatched
        return g
    if name == "span_already_filled":
        # span between endpoints already non-zero → no empty cells to fill
        g[1][2] = 4; g[2][2] = 4; g[3][2] = 4; g[4][2] = 4   # full column
        g[1][5] = 6; g[3][5] = 9; g[5][5] = 6                # midpoint already non-zero
        return g
    return g
