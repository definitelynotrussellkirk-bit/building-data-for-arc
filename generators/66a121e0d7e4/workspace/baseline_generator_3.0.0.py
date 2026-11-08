"""Generator for arc_additional_puzzles_21_set8:H56.

Rule: 8s in the first row/column select a submatrix; command 1..4
(at (0,0)) transforms it.

Combinatorial axes (8): grid_h, grid_w, palette_kind, cmd,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: no_8_markers, no_cmd, single_row_or_col.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "66a121e0d7e4"
VERSION = "3.0.0"  # out=2 shapes: gen FIXED 3 row markers [2,4,6] + 2 col markers [2,4] so submatrix was always 3x2 (output 3x2/2x3). Rule extracts |R|x|C| submatrix for ANY marker counts. Now vary n_rows/n_cols (1..4 each) and their positions -> output dims span 1x1..4x4 (rotated by cmd).
TASK_ID = "66a121e0d7e4"
SUMMARY = (
    "0-bg grid (h~7-10, w~8-12) with: "
    "(a) COMMAND CELL at (0, 0) painted "
    "with value cmd ∈ {1..4} encoding "
    "transform (1=identity / 2=flip / "
    "3=rot-CW / 4=rot-180); (b) ROW "
    "SELECTOR MARKERS — COLOR 8 cells "
    "in column 0 at rows from a fixed "
    "set [2, 4, 6] (3 row indices); "
    "(c) COLUMN SELECTOR MARKERS — "
    "COLOR 8 cells in row 0 at columns "
    "[2, 4] (2 col indices); (d) "
    "SUBMATRIX CELLS — at every (r, c) "
    "with r in row-selectors and c in "
    "col-selectors, a cell painted in "
    "a non-{0, 8, cmd} color (cycled "
    "from palette). The 8-markers "
    "define the submatrix rows × cols. "
    "Rule (READ ROW/COL SELECTORS, "
    "EXTRACT THE SUBMATRIX, APPLY CMD "
    "TRANSFORM): READ the SELECTORS — "
    "row indices R (cells in col 0 "
    "with value 8) and col indices C "
    "(cells in row 0 with value 8). "
    "EXTRACT the |R| × |C| SUBMATRIX "
    "from positions (R[i], C[j]). "
    "READ the CMD at (0, 0) and APPLY "
    "the corresponding TRANSFORM "
    "(identity / flip / rot-CW / rot-"
    "180). OUTPUT the transformed "
    "submatrix. Net: the submatrix "
    "picked by 8-markers is "
    "transformed per the (0, 0) cmd."
)

INVARIANTS = [
    "row and column selector markers are color 8",
    "selected cells form an |R| x |C| submatrix (any dims, incl. square)",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("no_8_markers", "no_cmd", "single_row_or_col")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 7..10", "valid": "6..14"},
    "grid_w":         {"type": "int", "default": "rng 8..12", "valid": "6..16"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "cmd":            {"type": "int", "default": "rng 1..4", "valid": "1..4"},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "1..7"},
    "position_bias":  {"type": "str", "default": "row_col_selectors",
                       "valid": "row_col_selectors"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "1..7"},
    "density":        {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 7, 9)
        w = ctx.draw_int("grid_w", 8, 10)
        cmd = ctx.draw_int("cmd", 1, 2)
        nr_hi, nc_hi = 3, 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 14)
        w = ctx.draw_int("grid_w", 12, 16)
        cmd = ctx.draw_int("cmd", 3, 4)
        nr_hi, nc_hi = 4, 4
    else:
        h = ctx.draw_int("grid_h", 8, 12)
        w = ctx.draw_int("grid_w", 9, 14)
        cmd = ctx.draw_int("cmd", 1, 4)
        nr_hi, nc_hi = 4, 4
    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    g[0][0] = cmd
    # vary the submatrix dimensions: |R| row-markers in col 0, |C| col-markers
    # in row 0, at random (distinct, sorted) positions -> output dims vary.
    n_rows = ctx.draw_int("n_rows", 1, min(nr_hi, h - 1))
    n_cols = ctx.draw_int("n_cols", 1, min(nc_hi, w - 1))
    rows = sorted(rng.sample(range(1, h), n_rows))
    cols = sorted(rng.sample(range(1, w), n_cols))
    for r in rows:
        g[r][0] = 8
    for c in cols:
        g[0][c] = 8
    colors = [v for v in range(1, 10) if v not in (8, cmd)]
    for rr, r in enumerate(rows):
        for cc, c in enumerate(cols):
            g[r][c] = colors[(rr * len(cols) + cc + rng.randint(0, 3)) % len(colors)]
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 10
    g = full_grid(h, w, 0)
    if name == "no_8_markers":
        # cmd present but no row/col selectors → no submatrix to extract
        g[0][0] = 2
        for r, c in [(2, 2), (2, 4), (4, 2), (4, 4)]:
            g[r][c] = 6
        return g
    if name == "no_cmd":
        # selectors present but no cmd at (0,0) → transform is undefined
        for r in [2, 4]: g[r][0] = 8
        for c in [2, 4]: g[0][c] = 8
        for rr, r in enumerate([2, 4]):
            for cc, c in enumerate([2, 4]):
                g[r][c] = 3 + rr + cc
        return g
    if name == "single_row_or_col":
        # only one row marker → submatrix collapses to a 1-row strip
        g[0][0] = 2
        g[3][0] = 8
        for c in [2, 4]: g[0][c] = 8
        g[3][2] = 5; g[3][4] = 6
        return g
    return g
