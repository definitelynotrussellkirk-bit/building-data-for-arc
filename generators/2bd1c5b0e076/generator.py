"""Generator for arc_additional_puzzle_bank_volume8:M54.

Rule: row 0 has 1-cells (cols) and 2-cells (cols); col 0 has 1-cells
(rows) and 2-cells (rows). Paint 3 at intersections of red rows/cols,
8 at intersections of blue rows/cols.

Combinatorial axes (8): grid_h, grid_w, palette_kind, n_markers,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_row_markers, missing_col_markers, parallel_only.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2bd1c5b0e076"
VERSION = "2.1.0"  # FIX: normal path now realizes the documented 2+2 row/col marker counts
TASK_ID = "2bd1c5b0e076"
SUMMARY = (
    "0-bg grid (h ∈ 7-9, w ∈ 9-11) with: "
    "(a) ROW 0 markers at FIXED cols — "
    "g[0][3] = g[0][6] = 1 (COLOR-1 "
    "BLUE markers in cols 3, 6); "
    "g[0][4] = g[0][7] = 2 (COLOR-2 "
    "RED markers in cols 4, 7); "
    "(b) COL 0 markers at FIXED rows — "
    "g[1][0] = g[2][0] = 2 (red "
    "markers in rows 1, 2); "
    "g[3][0] = g[4][0] = 1 (blue "
    "markers in rows 3, 4); (c) ONE "
    "COLOR-6 (MAGENTA) DECORATION at "
    "(h-1, w-1). Rule (PAINT 3 AT "
    "INTERSECTIONS OF BLUE ROWS WITH "
    "BLUE COLS, PAINT 8 AT "
    "INTERSECTIONS OF RED ROWS WITH "
    "RED COLS): READ row 0 to "
    "extract BLUE_COLS = cols where "
    "g[0][c] == 1, RED_COLS = cols "
    "where g[0][c] == 2. READ col 0 "
    "to extract BLUE_ROWS = rows "
    "where g[r][0] == 1, RED_ROWS = "
    "rows where g[r][0] == 2. For "
    "EACH (br, bc) ∈ BLUE_ROWS × "
    "BLUE_COLS: PAINT g[br][bc] = "
    "COLOR 3 (green). For EACH "
    "(rr, rc) ∈ RED_ROWS × RED_COLS: "
    "PAINT g[rr][rc] = COLOR 8 "
    "(cyan). Net: same-color "
    "borders project intersections "
    "in distinct colors — blue×"
    "blue → green, red×red → cyan."
)

INVARIANTS = [
    "row 0 (cols ≥ 1) has 2-cells of color 1 and 2-cells of color 2",
    "col 0 (rows ≥ 1) has 2-cells of color 1 and 2-cells of color 2",
    "decoration is non-{0,1,2,3,8} cell elsewhere",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_row_markers", "missing_col_markers", "parallel_only")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..9", "valid": "5..14"},
    "grid_w":         {"type": "int", "default": "rng 9..11", "valid": "5..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_markers":      {"type": "int", "default": "2_per_color", "valid": "2_per_color"},
    "palette_size":   {"type": "int", "default": "3", "valid": "3"},
    "position_bias":  {"type": "str", "default": "axis_markers",
                       "valid": "axis_markers"},
    "n_distinct_colors": {"type": "int", "default": "3", "valid": "3"},
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
        h = ctx.draw_int("grid_h", 7, 8)
        w = ctx.draw_int("grid_w", 9, 10)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 8, 9)
        w = ctx.draw_int("grid_w", 10, 11)
    else:
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 9, 11)
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    # Realize the documented/count-map invariant: two markers of each
    # source color on each axis. Earlier versions sampled 1..2 and leaked
    # under-specified one-marker rows/cols into the normal path.
    n_blue_cols = 2
    n_red_cols = 2
    col_positions = rng.sample(range(1, w), n_blue_cols + n_red_cols)
    rng.shuffle(col_positions)
    for c in col_positions[:n_blue_cols]:
        g[0][c] = 1
    for c in col_positions[n_blue_cols:]:
        g[0][c] = 2
    # Two rows for each source color as well.
    n_blue_rows = 2
    n_red_rows = 2
    row_positions = rng.sample(range(1, h), n_blue_rows + n_red_rows)
    rng.shuffle(row_positions)
    for r in row_positions[:n_blue_rows]:
        g[r][0] = 1
    for r in row_positions[n_blue_rows:]:
        g[r][0] = 2
    # Optional decoration at random corner (60% prob)
    if rng.random() < 0.6:
        corners = [(0, w - 1), (h - 1, 0), (h - 1, w - 1)]
        cr, cc = rng.choice(corners)
        if g[cr][cc] == 0:
            g[cr][cc] = rng.choice([4, 5, 6, 7])
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "missing_row_markers":
        # row 0 has no 1/2 markers → no candidate columns, no intersections
        g[1][0] = 2; g[2][0] = 2
        g[3][0] = 1; g[4][0] = 1
        return g
    if name == "missing_col_markers":
        # col 0 has no 1/2 markers → no candidate rows, no intersections
        g[0][3] = 1; g[0][6] = 1
        g[0][4] = 2; g[0][7] = 2
        return g
    if name == "parallel_only":
        # only one color present on both axes → only one set of intersections, the other is empty
        g[0][3] = 1; g[0][6] = 1
        g[3][0] = 1; g[4][0] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Executable invariants for same-color axis intersections."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    h = len(grid)
    errors = []
    row1 = sum(1 for c in range(1, w) if grid[0][c] == 1)
    row2 = sum(1 for c in range(1, w) if grid[0][c] == 2)
    col1 = sum(1 for r in range(1, h) if grid[r][0] == 1)
    col2 = sum(1 for r in range(1, h) if grid[r][0] == 2)
    if (row1, row2, col1, col2) != (2, 2, 2, 2):
        errors.append(f"expected two 1/2 markers on each axis, got {(row1, row2, col1, col2)}")
    for r in range(1, h):
        for c in range(1, w):
            if grid[r][c] in (3, 8):
                errors.append("output colors 3/8 should not appear in the input")
                return sorted(set(errors))
    return sorted(set(errors))
