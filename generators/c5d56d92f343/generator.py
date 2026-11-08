"""Generator for v3_rich_schema:easy_04_intersections_from_markers — paint intersections.

Rule: row 0 has color-1 markers at some columns; column 0 has color-2
markers at some rows. Output paints color 4 at every (r, c) where
both markers exist.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_col, n_row,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_col_markers, no_row_markers, marker_color_swap.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c5d56d92f343"
VERSION = "1.3.0"
TASK_ID = "c5d56d92f343"
SUMMARY = "Row 0 has color-1 column markers at some columns; column 0 has color-2 row markers at some rows. Rule paints color 4 at every (r, c) where row 0 has a 1 at column c AND column 0 has a 2 at row r. Markers preserved."

# Rivals: 'output is input' refuted by any demo with markers in both axes.
# 'paint with color 1 or 2 at intersections' refuted by any demo (it's 4).
# 'paint entire row/col' refuted by any demo (only intersection cells).
# 'paint outside row 0 + col 0' refuted by ≥1 demo where bg cells off
# the marker rows/cols stay 0. 3 demos with varied marker counts cover.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "background is 0",
    "row 0 has at least two color-1 markers at distinct columns ≥ 1",
    "column 0 has at least two color-2 markers at distinct rows ≥ 1",
    "no colored cells appear outside the marker row/column",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_col_markers", "no_row_markers", "marker_color_swap")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 5..8", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 6..9", "valid": "5..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_col":          {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "n_row":          {"type": "int", "default": "rng 2..4", "valid": "2..6"},
    "palette_size":   {"type": "int", "default": "2", "valid": "2..3"},
    "position_bias":  {"type": "str", "default": "row0_col0_markers",
                       "valid": "row0_col0_markers"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2..3"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 4, 7)
        w = ctx.draw_int("grid_w", 5, 8)
        n_col = ctx.draw_int("n_col", 2, 3)
        n_row = ctx.draw_int("n_row", 2, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 10, 14)
        w = ctx.draw_int("grid_w", 11, 16)
        n_col = ctx.draw_int("n_col", 4, 6)
        n_row = ctx.draw_int("n_row", 4, 6)
    else:
        h = ctx.draw_int("grid_h", 7, 10)
        w = ctx.draw_int("grid_w", 8, 12)
        n_col = ctx.draw_int("n_col", 2, 4)
        n_row = ctx.draw_int("n_row", 2, 4)
    rng = ctx.draw_rng("layout")

    n_col = min(n_col, w - 1)
    n_row = min(n_row, h - 1)

    g = full_grid(h, w, 0)
    cols = rng.sample(range(1, w), n_col)
    for c in cols:
        g[0][c] = 1
    rows = rng.sample(range(1, h), n_row)
    for r in rows:
        g[r][0] = 2
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable marker-intersection invariants for normal inputs."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    row0_ones = [c for c in range(1, w) if grid[0][c] == 1]
    col0_twos = [r for r in range(1, h) if grid[r][0] == 2]
    if len(row0_ones) < 2:
        errors.append(f"row 0 has only {len(row0_ones)} color-1 column marker(s)")
    if len(col0_twos) < 2:
        errors.append(f"col 0 has only {len(col0_twos)} color-2 row marker(s)")
    bad_row0 = [(0, c, grid[0][c]) for c in range(1, w)
                if grid[0][c] not in (0, 1)]
    bad_col0 = [(r, 0, grid[r][0]) for r in range(1, h)
                if grid[r][0] not in (0, 2)]
    interior = [(r, c, grid[r][c]) for r in range(1, h) for c in range(1, w)
                if grid[r][c] != 0]
    if grid[0][0] != 0:
        errors.append("origin marker cell (0,0) should stay background")
    if bad_row0:
        errors.append(f"row 0 contains non-marker colors: {bad_row0[:3]}")
    if bad_col0:
        errors.append(f"col 0 contains non-marker colors: {bad_col0[:3]}")
    if interior:
        errors.append(f"input has colored interior cells before intersection fill: {interior[:3]}")
    return errors


def _draw_from_degenerate(name, rng):
    h, w = 7, 8
    g = full_grid(h, w, 0)
    if name == "no_col_markers":
        # only row markers, no column markers → no intersections, output has no 4s
        for r in [2, 4, 5]: g[r][0] = 2
        return g
    if name == "no_row_markers":
        # only column markers, no row markers → no intersections, output has no 4s
        for c in [2, 4, 6]: g[0][c] = 1
        return g
    if name == "marker_color_swap":
        # row markers use color 2 in row 0, col markers use color 1 in col 0 (swapped roles)
        for c in [2, 5]: g[0][c] = 2   # wrong color in row 0
        for r in [2, 4]: g[r][0] = 1   # wrong color in col 0
        return g
    return g
