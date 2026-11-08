"""Generator for arc_puzzle_bank_21_set21_bundle:easy_p07 — border markers project crosshairs.

Rule: left-border row markers and top-border column markers form
crosshair projections.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_markers, only_row_markers, only_col_markers.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3faff4c1f734"
VERSION = "2.0.1"
TASK_ID = "3faff4c1f734"
SUMMARY = (
    "0-bg grid (h~6-9, w~7-10) "
    "with: (a) 2-3 ROW MARKERS "
    "on the LEFT BORDER (col 0) "
    "at distinct rows ≥1, each "
    "in a DISTINCT color; (b) "
    "2-3 COL MARKERS on the "
    "TOP BORDER (row 0) at "
    "distinct cols ≥1, each in "
    "a DISTINCT color. Top-left "
    "(0, 0) stays 0. All marker "
    "colors are unique across "
    "row + col markers. Rule "
    "(PROJECT CROSSHAIRS): "
    "identify ROW MARKERS "
    "(left-border non-0 cells) "
    "and COL MARKERS (top-"
    "border non-0 cells). For "
    "EACH row marker at "
    "(r, 0) with color C, "
    "PAINT the entire row r "
    "with C. For EACH col "
    "marker at (0, c) with "
    "color D, PAINT the entire "
    "column c with D. At "
    "intersections (row marker "
    "and col marker meeting), "
    "task-specific tiebreak. "
    "Net: border markers shoot "
    "crosshair beams across "
    "the grid."
)

INVARIANTS = [
    "background is 0",
    "top-left is zero",
    "left-border markers paint rows, top-border markers paint columns",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_markers", "only_row_markers", "only_col_markers")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..9", "valid": "4..12"},
    "grid_w":         {"type": "int", "default": "rng 7..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "row_markers":    {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "col_markers":    {"type": "int", "default": "rng 2..3", "valid": "1..8"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "border_markers",
                       "valid": "border_markers"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: cell(0,0) == 0, >=1 left-border row marker (col 0, row >=1, nonzero), >=1 top-border col marker."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 30 or w > 30:
        errs.append(f"grid too large: {h}x{w}")
    texture = (meta or {}).get("texture", "")
    if texture in DEGENERATE_TEXTURES:
        return errs
    if grid[0][0] != 0:
        errs.append(f"cell (0,0) expected to be 0, found {grid[0][0]}")
    row_markers = [r for r in range(1, h) if grid[r][0] != 0]
    col_markers = [c for c in range(1, w) if grid[0][c] != 0]
    if not row_markers:
        errs.append("no left-border row markers (col 0, row >=1, nonzero) found")
    if not col_markers:
        errs.append("no top-border col markers (row 0, col >=1, nonzero) found")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 7, 8)
        row_markers = min(ctx.draw_int("row_markers", 2, 2), h - 1)
        col_markers = min(ctx.draw_int("col_markers", 2, 2), w - 1)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 9, 10)
        row_markers = min(ctx.draw_int("row_markers", 3, 3), h - 1)
        col_markers = min(ctx.draw_int("col_markers", 3, 3), w - 1)
    else:
        h = ctx.draw_int("grid_h", 6, 9)
        w = ctx.draw_int("grid_w", 7, 10)
        row_markers = min(ctx.draw_int("row_markers", 2, 3), h - 1)
        col_markers = min(ctx.draw_int("col_markers", 2, 3), w - 1)
    rng = ctx.draw_rng("layout")
    grid = full_grid(h, w, 0)
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8, 9], row_markers + col_markers)

    rows = rng.sample(range(1, h), row_markers)
    cols = rng.sample(range(1, w), col_markers)
    for idx, r in enumerate(rows):
        grid[r][0] = colors[idx]
    for idx, c in enumerate(cols, start=row_markers):
        grid[0][c] = colors[idx]
    return grid


def _draw_from_degenerate(name, rng):
    h, w = 7, 9
    g = full_grid(h, w, 0)
    if name == "no_markers":
        # blank → no projections to draw
        return g
    if name == "only_row_markers":
        # row markers but no column markers → only horizontal projections
        g[1][0] = 4
        g[3][0] = 6
        g[5][0] = 7
        return g
    if name == "only_col_markers":
        # column markers but no row markers → only vertical projections
        g[0][2] = 4
        g[0][5] = 6
        g[0][8] = 7
        return g
    return g
