"""Generator for E21: mark endpoints of same-color line segments.

Rule: cells with exactly one same-color cardinal neighbor are line
endpoints and recolor to 8.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_lines,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_lines, all_singletons, dense_branching.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "af13a88bfcbe"
VERSION = "2.0.1"
TASK_ID = "af13a88bfcbe"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) "
    "with 2-4 STRAIGHT LINE "
    "SEGMENTS (horizontal or "
    "vertical, length 2-4 cells) "
    "in DISTINCT colors. Lines "
    "are placed at spaced "
    "positions so they don't "
    "touch. Rule (MARK LINE "
    "ENDPOINTS WITH COLOR 8): "
    "for EACH non-zero CELL, "
    "COUNT its same-color "
    "CARDINAL (4-conn) "
    "NEIGHBORS. If the count is "
    "EXACTLY 1 (the cell has "
    "only one same-color "
    "neighbor — it's a line "
    "endpoint), RECOLOR it to "
    "COLOR 8 (cyan). Interior "
    "cells (2 same-color "
    "neighbors) keep their "
    "color. Singletons (0 "
    "neighbors) keep their "
    "color. Net: each line "
    "segment's two endpoints "
    "become cyan."
)

INVARIANTS = [
    "line segments are straight and separated",
    "segment length is at least two",
    "background is zero",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_lines", "all_singletons", "dense_branching")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": 'default|warm|cool|varied'},
    "n_lines":        {"type": "int", "default": "rng 2..4", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "grid_aligned",
                       "valid": "grid_aligned"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..4", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": 'default|warm|cool|varied|no_lines|all_singletons|dense_branching'},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0, at least one nonzero cell (line segments), no color-8 in input."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    texture = (meta or {}).get("texture", "")
    if texture in ("no_lines",):
        return []
    errs = []
    h = len(grid)
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    has_nonzero = any(grid[r][c] != 0 for r in range(h) for c in range(w))
    has_8 = any(grid[r][c] == 8 for r in range(h) for c in range(w))
    if not has_nonzero:
        errs.append("no line-segment cells found")
    if has_8:
        errs.append("color-8 present in input (rule writes 8 for endpoints)")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 8, 10)
        n = ctx.draw_int("n_lines", 2, 2)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 11, 12)
        n = ctx.draw_int("n_lines", 3, 4)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n = ctx.draw_int("n_lines", 2, 4)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    spots = [(r, c) for r in range(1, h - 1, 3) for c in range(1, w - 3, 4)]
    rng.shuffle(spots)
    for i, (r, c) in enumerate(spots[:n]):
        color = (i % 7) + 1
        length = rng.randint(2, 4)
        if rng.random() < 0.5 and c + length < w:
            for cc in range(c, c + length):
                g[r][cc] = color
        else:
            for rr in range(r, min(h, r + length)):
                g[rr][c] = color
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_lines":
        # empty grid → no segments, no endpoints to mark
        return g
    if name == "all_singletons":
        # only single cells → degree-0 cells are not endpoints (need ≥1 same-color neighbor)
        g[1][2] = 4
        g[3][5] = 6
        g[5][7] = 7
        return g
    if name == "dense_branching":
        # cell with 2+ same-color neighbors (T-junction) → not an endpoint, rule misses it
        for r, c in [(2, 2), (2, 3), (2, 4), (3, 3), (4, 3)]: g[r][c] = 5
        return g
    return g
