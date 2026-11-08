"""Generator for arc_additional_puzzle_bank_volume9:E58 — complete blue 2x2 L-shapes with green.

Rule: blue 2×2 L-shapes are completed by filling the missing cell green.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_shapes,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_shapes, all_solid_squares, mixed_color_corners.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "3a379d1ed52c"
VERSION = "2.0.1"
TASK_ID = "3a379d1ed52c"
SUMMARY = (
    "0-bg grid (h, w~7-12) "
    "with 2-5 BLUE(1) L-"
    "TROMINOES (3-cell L-"
    "shapes in 2×2 bboxes "
    "with one missing "
    "corner). L-trominoes "
    "are placed at "
    "ANCHOR-GRID positions "
    "(every 3 cells starting "
    "at row 0, col 0), each "
    "with a RANDOM MISSING "
    "CORNER (one of 4 "
    "orientations). Each "
    "L-tromino occupies 3 "
    "of 4 cells in its 2×2 "
    "bbox, leaving the "
    "missing corner at 0. "
    "Rule (FILL EACH 2×2 "
    "WINDOW WITH 3 BLUES + "
    "1 BG CELL → GREEN AT "
    "THE BG CELL): scan "
    "EVERY 2×2 WINDOW in "
    "the grid. For EACH "
    "window containing "
    "EXACTLY 3 BLUE(1) "
    "CELLS AND 1 BG(0) "
    "CELL: PAINT the bg "
    "cell at (r, c) with "
    "COLOR 3 (green). "
    "Windows with other "
    "blue-counts (0, 1, 2, "
    "4) stay unchanged. "
    "Net: every L-tromino "
    "completes to a 2×2 "
    "solid by adding a "
    "green dot in the "
    "missing corner."
)

# Rivals: 'fill all bg cells' refuted by ≥1 demo with bg cells in
# non-L windows staying 0. 'fill with blue' refuted by any demo
# (fill is green). 'fill solid 2×2 too' refuted by any demo (only
# 3-blue windows trigger). 'fill with 2-blue or 1-blue too' refuted
# similarly.
# 4 demos with varied L positions cover this.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0",
    "each target 2x2 window contains exactly three blue cells",
    "target windows are separated from one another",
    "missing cells are blank before the rule runs",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_shapes", "all_solid_squares", "mixed_color_corners")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..12", "valid": "4..24"},
    "grid_w":         {"type": "int", "default": "rng 7..12", "valid": "4..24"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_shapes":       {"type": "int", "default": "rng 2..5", "valid": "1..12"},
    "palette_size":   {"type": "int", "default": "1", "valid": "1..1"},
    "position_bias":  {"type": "str", "default": "spaced_blue_L_trominoes",
                       "valid": "spaced_blue_L_trominoes"},
    "n_distinct_colors": {"type": "int", "default": "1", "valid": "1..1"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: bg=0; ≥3 blue (color-1) L-tromino cells (3 per L in 2x2 bbox); values 0..9."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errors = []
    for r in range(h):
        for c in range(w):
            if not (0 <= grid[r][c] <= 9):
                errors.append(f"out-of-range value {grid[r][c]} at ({r},{c})")
    blues = sum(1 for r in range(h) for c in range(w) if grid[r][c] == 1)
    if blues == 0:
        pass  # degenerate (no_shapes) — allowed
    elif blues % 3 != 0:
        errors.append(f"blue cell count {blues} not a multiple of 3 (each L has 3 cells)")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 5, 8)
        w = ctx.draw_int("grid_w", 5, 8)
        n_shapes = ctx.draw_int("n_shapes", 1, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 18)
        w = ctx.draw_int("grid_w", 13, 18)
        n_shapes = ctx.draw_int("n_shapes", 6, 10)
    else:
        h = ctx.draw_int("grid_h", 9, 12)
        w = ctx.draw_int("grid_w", 9, 12)
        n_shapes = ctx.draw_int("n_shapes", 3, 6)
    rng = ctx.draw_rng("placement")
    g = full_grid(h, w, 0)
    anchors = [(r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)]
    rng.shuffle(anchors)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for r, c in anchors[:n_shapes]:
        missing = rng.choice(corners)
        for dr, dc in corners:
            if (dr, dc) != missing:
                g[r + dr][c + dc] = 1
    if not any(1 in row for row in g):
        g[0][0] = 1
        g[0][1] = 1
        g[1][0] = 1
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_shapes":
        # blank → no L-shapes to complete
        return g
    if name == "all_solid_squares":
        # 2x2 fully filled with blue → no missing cell to fill
        for r in range(2):
            for c in range(2): g[1 + r][1 + c] = 1
        for r in range(2):
            for c in range(2): g[4 + r][4 + c] = 1
        return g
    if name == "mixed_color_corners":
        # 2x2 with 3 cells but mixed colors → "all blue" precondition fails
        g[1][1] = 1; g[1][2] = 4; g[2][1] = 1   # mixed
        g[4][4] = 6; g[4][5] = 1; g[5][4] = 1   # mixed
        return g
    return g
