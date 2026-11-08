"""Generator for arc_puzzle_bank_sixth21:E38.

Rule: top-row column headers recolor body cells marked with 8 in the
same column.

Combinatorial axes (8): grid_h/w, palette_kind, n_columns, palette_size,
position_bias, n_distinct_colors, marker_density, texture.
Degenerates: no_headers, no_markers, markers_in_empty_columns.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "c22ce0168b97"
VERSION = "2.0.1"
TASK_ID = "c22ce0168b97"
SUMMARY = (
    "0-bg grid (h, w~6-10) with: (a) "
    "TOP ROW (row 0) containing 2-5 "
    "COLOR HEADERS at random distinct "
    "columns, in DISTINCT non-{0, 8} "
    "colors; (b) BODY (rows 1..h-1) "
    "with 1-3 COLOR-8 MARKER CELLS in "
    "each header column at random rows. "
    "Columns without headers stay 0. "
    "Rule (HEADER-DIRECTED RECOLOR): "
    "for EACH COLUMN c where row 0 "
    "contains a NON-ZERO HEADER COLOR "
    "header_c, find all body cells in "
    "that column with value 8 and "
    "RECOLOR them to header_c. The "
    "top-row header stays. Cells in "
    "header-less columns and non-8 "
    "body cells stay. Net: top-row "
    "color tags propagate down their "
    "column to repaint every 8-marker."
)

INVARIANTS = [
    "top row contains nonzero column headers",
    "body markers use color 8",
    "background is zero",
]

PALETTE_KINDS = ("default", "sparse", "dense", "varied_palette")
DEGENERATE_TEXTURES = ("no_headers", "no_markers", "markers_in_empty_columns")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "grid_h":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "grid_w":         {"type": "int", "default": "rng 6..10", "valid": "4..14"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "n_columns":      {"type": "int", "default": "rng 2..5", "valid": "1..10"},
    "palette_size":   {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "position_bias":  {"type": "str", "default": "spread", "valid": "spread"},
    "n_distinct_colors": {"type": "int", "default": "rng 2..5", "valid": "1..8"},
    "marker_density": {"type": "str", "default": "mixed", "valid": "mixed"},
    "texture":        {"type": "str", "default": "alias for palette_kind",
                       "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: top row has non-zero non-8 headers; body has color-8 marker cells."""
    if not grid or not grid[0]:
        return ["empty grid"]
    w = len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    h = len(grid)
    headers = [c for c in range(w) if grid[0][c] not in (0, 8)]
    body_eights = [(r, c) for r in range(1, h) for c in range(w) if grid[r][c] == 8]
    if not headers:
        errs.append("no non-{0,8} column headers in top row")
    if not body_eights:
        errs.append("no color-8 marker cells in body rows")
    return errs


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], None)
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 6, 7)
        w = ctx.draw_int("grid_w", 6, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 9, 10)
        w = ctx.draw_int("grid_w", 9, 10)
    else:
        h = ctx.draw_int("grid_h", 6, 10)
        w = ctx.draw_int("grid_w", 6, 10)
    n = min(ctx.draw_int("n_columns", 2, 5), w)
    rng = ctx.draw_rng("layout")
    colors = list(ctx.draw_distinct_colors("colors", n=n, exclude={0, 8}))
    cols = list(range(w))
    rng.shuffle(cols)
    g = full_grid(h, w, 0)
    for i, c in enumerate(cols[:n]):
        g[0][c] = colors[i]
        for r in rng.sample(range(1, h), rng.randint(1, min(3, h - 1))):
            g[r][c] = 8
    return g


def _draw_from_degenerate(name, rng):
    h, w = 8, 8
    g = full_grid(h, w, 0)
    if name == "no_headers":
        # markers exist but no top-row headers → recolor source undefined
        g[3][2] = 8
        g[5][5] = 8
        return g
    if name == "no_markers":
        # headers but no body 8-markers → rule has nothing to recolor
        g[0][2] = 4
        g[0][5] = 7
        return g
    if name == "markers_in_empty_columns":
        # 8-markers in cols where header is 0 → ambiguous (recolor to bg?)
        g[0][3] = 5
        g[2][1] = 8  # body marker in col 1 where header[0][1]=0
        g[5][7] = 8  # body marker in col 7 where header[0][7]=0
        return g
    return g
