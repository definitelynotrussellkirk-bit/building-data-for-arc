"""Generator for arc_puzzle_bank_twelfth21:E84.

Rule: rows above a full 9 separator are mirrored into the rows below it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, density,
palette_size, position_bias, n_distinct_colors, cells, texture.
Degenerates: empty_top, full_top, sep_at_top.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c8138b7e476c"
VERSION = "2.0.1"
TASK_ID = "c8138b7e476c"
SUMMARY = (
    "0-bg grid with HEIGHT = "
    "2*half + 1 (half~3-5) and "
    "WIDTH~7-12. Layout: (a) "
    "ONE FULL ROW of COLOR-9 "
    "(maroon) at row 'half' "
    "(the separator); (b) "
    "TOP HALF (rows 0..half-1) "
    "contains 5-9 scattered "
    "cells in random colors "
    "from {1..8} at distinct "
    "positions; (c) BOTTOM "
    "HALF (rows half+1..h-1) "
    "is all 0. Top half and "
    "bottom half are "
    "symmetric in size around "
    "the separator. Rule "
    "(MIRROR TOP HALF DOWN "
    "ACROSS 9-SEPARATOR): "
    "identify the FULL-9 "
    "SEPARATOR ROW at index "
    "'half'. For EACH non-0 "
    "cell (r, c) in the TOP "
    "HALF (r < half), PAINT "
    "the MIRROR position "
    "(2*half - r, c) with "
    "the same color. Top "
    "half + separator stay. "
    "Net: top-half cells "
    "reflect down across the "
    "maroon separator into "
    "the bottom half."
)

INVARIANTS = [
    "background is 0",
    "there is one full separator row of 9s",
    "the grid has equal space above and below the separator",
    "only the top half contains source nonzero cells",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("empty_top", "full_top", "sep_at_top")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {'grid_h': {'type': 'int', 'default': 'rng 7..11 (=2*half+1)', 'valid': '3..19'},
 'grid_w': {'type': 'int', 'default': 'rng 7..12', 'valid': '3..24'},
 'palette_kind': {'type': 'str', 'default': 'rng helpful', 'valid': 'default|warm|cool|varied'},
 'density': {'type': 'str', 'default': 'mixed', 'valid': 'mixed'},
 'palette_size': {'type': 'int', 'default': 'rng 1..6', 'valid': '1..8'},
 'position_bias': {'type': 'str', 'default': 'top_half', 'valid': 'top_half'},
 'n_distinct_colors': {'type': 'int', 'default': 'rng 1..6', 'valid': '1..8'},
 'cells': {'type': 'int', 'default': 'rng 5..9', 'valid': '1..30'},
 'texture': {'type': 'str',
             'default': 'alias for palette_kind',
             'valid': 'default|warm|cool|varied|empty_top|full_top|sep_at_top'}}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        half = ctx.draw_int("half_h", 3, 4)
        w = ctx.draw_int("grid_w", 7, 9)
        count = ctx.draw_int("cells", 4, 6)
    elif difficulty == "hard":
        half = ctx.draw_int("half_h", 4, 5)
        w = ctx.draw_int("grid_w", 10, 12)
        count = ctx.draw_int("cells", 7, 10)
    else:
        half = ctx.draw_int("half_h", 3, 5)
        w = ctx.draw_int("grid_w", 7, 12)
        count = ctx.draw_int("cells", 5, 9)
    rng = ctx.draw_rng("layout")
    h = half * 2 + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[half][c] = 9
    choices = [(r, c) for r in range(half) for c in range(w)]
    rng.shuffle(choices)
    for r, c in choices[:min(count, len(choices))]:
        g[r][c] = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Grid must have a full-row-of-9 separator and non-zero cells only in the top half."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    # Find the separator row (full row of 9)
    sep = None
    for r in range(h):
        if all(grid[r][c] == 9 for c in range(w)):
            sep = r
            break
    if sep is None:
        msgs.append("no full-row-of-9 separator found")
        return msgs
    # Bottom half should be all 0
    for r in range(sep + 1, h):
        for c in range(w):
            if grid[r][c] != 0:
                msgs.append(f"bottom half has non-zero cell at ({r},{c}) (expected all-bg before mirror)")
                return msgs
    # Top half must have at least one non-zero cell
    top_nz = any(grid[r][c] != 0 for r in range(sep) for c in range(w))
    if not top_nz:
        msgs.append("top half has no non-zero cells to mirror")
    return msgs


def _draw_from_degenerate(name, rng):
    half, w = 4, 9
    h = half * 2 + 1
    g = full_grid(h, w, 0)
    for c in range(w):
        g[half][c] = 9
    if name == "empty_top":
        # separator only — nothing to mirror
        return g
    if name == "full_top":
        # entire top half filled — output mirror leaves no bg
        for r in range(half):
            for c in range(w):
                g[r][c] = ((r + c) % 7) + 1
        return g
    if name == "sep_at_top":
        # separator on row 0 → no top half exists, rule has empty source
        g = full_grid(h, w, 0)
        for c in range(w):
            g[0][c] = 9
        for r in range(1, h):
            g[r][0] = 5
        return g
    return g
