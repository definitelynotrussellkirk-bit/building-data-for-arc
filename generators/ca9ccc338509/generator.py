"""Generator for arc_additional_puzzles_21_set14_bundle:M92 — Checkerboard alternating row/col keys.

Rule: row-keys = col 0 values (rows 1+); col-keys = row 0 values
(cols 1+). Output is 2N × 2M where (r,c) is row-key[r//2] if (r+c)
even, col-key[c//2] otherwise.

Combinatorial axes (8): n_rows, n_cols, palette_kind,
palette_size, position_bias, n_distinct_colors, density, texture.
Degenerates: missing_row_keys, missing_col_keys, all_same_color.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ca9ccc338509"
VERSION = "1.2.2"  # keep default keys from collapsing to the all_same_color degenerate
TASK_ID = "ca9ccc338509"
SUMMARY = "Input is (N+1) × (M+1). Row 0 cols 1..M hold M col-key colors; col 0 rows 1..N hold N row-key colors. (0,0) is 0. Rule emits a 2N × 2M grid: at output (r, c), use row-key[r//2] if (r+c) is even, else col-key[c//2]. The output is a 2-cell-thick checkerboard mixing the row and col keys."

# Rivals: 'output is input' refuted by demos (output is 2N x 2M).
# 'output is 1x1 scaling' refuted by demos (scale factor is 2).
# 'use only row keys' refuted by demos with col-key cells visible.
# 'pure replication' refuted by demos with alternation pattern.
# 3 demos with N≥2 and M≥2 cover this.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "row 0 (cols 1+) holds 1..3 distinct color values",
    "col 0 (rows 1+) holds 1..3 distinct color values",
    "(0,0) is 0",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
DEGENERATE_TEXTURES = ("missing_row_keys", "missing_col_keys", "all_same_color")
HELPFUL_TEXTURES = PALETTE_KINDS

AXES = {
    "n_rows":         {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "n_cols":         {"type": "int", "default": "rng 2..3", "valid": "1..7"},
    "palette_kind":   {"type": "str", "default": "rng helpful",
                       "valid": "|".join(PALETTE_KINDS)},
    "palette_size":   {"type": "int", "default": "rng 4..6", "valid": "2..9"},
    "position_bias":  {"type": "str", "default": "row0_col0_keys",
                       "valid": "row0_col0_keys"},
    "n_distinct_colors": {"type": "int", "default": "rng 4..6", "valid": "2..9"},
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
        n_rows = ctx.draw_int("n_rows", 2, 3)
        n_cols = ctx.draw_int("n_cols", 2, 3)
    elif difficulty == "hard":
        n_rows = ctx.draw_int("n_rows", 4, 7)
        n_cols = ctx.draw_int("n_cols", 4, 7)
    else:
        n_rows = ctx.draw_int("n_rows", 3, 5)
        n_cols = ctx.draw_int("n_cols", 3, 5)
    h = n_rows + 1; w = n_cols + 1
    g = full_grid(h, w, 0)
    rng = ctx.draw_rng("layout")
    color_rng = ctx.draw_rng("colors")
    for r in range(1, h):
        g[r][0] = color_rng.randint(1, 9)
    for c in range(1, w):
        g[0][c] = color_rng.randint(1, 9)
    # Avoid leaking the declared all_same_color degenerate into normal data:
    # if every row/col key is identical, the 2x checkerboard output is a
    # uniform block and no alternation branch is visible.
    keys = [g[r][0] for r in range(1, h)] + [g[0][c] for c in range(1, w)]
    if len(set(keys)) == 1:
        old = keys[0]
        choices = [v for v in range(1, 10) if v != old]
        g[0][w - 1] = choices[color_rng.randrange(len(choices))]
    return g


def _draw_from_degenerate(name, rng):
    if name == "missing_row_keys":
        # col 0 (rows 1+) is blank → no row-key palette; checkerboard's "even" cells are 0
        h, w = 4, 4
        g = full_grid(h, w, 0)
        g[0][1] = 4; g[0][2] = 6; g[0][3] = 3
        # col 0 stays blank
        return g
    if name == "missing_col_keys":
        # row 0 (cols 1+) is blank → no col-key palette; checkerboard's "odd" cells are 0
        h, w = 4, 4
        g = full_grid(h, w, 0)
        # row 0 stays blank
        g[1][0] = 4; g[2][0] = 6; g[3][0] = 3
        return g
    if name == "all_same_color":
        # all keys identical → output checkerboard collapses to a uniform color (no pattern)
        h, w = 4, 4
        g = full_grid(h, w, 0)
        for c in range(1, w): g[0][c] = 5
        for r in range(1, h): g[r][0] = 5
        return g
    return full_grid(4, 4, 0)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row-0 (cols 1+) and col-0 (rows 1+) must each be non-zero keys; interior (1+,1+) must be all-zero."""
    msgs = []
    h = len(grid)
    w = len(grid[0]) if h else 0
    if h < 2 or w < 2:
        msgs.append("grid too small (need >=2x2)")
        return msgs
    # Row 0 col keys (cols 1+) must all be non-zero
    if any(grid[0][c] == 0 for c in range(1, w)):
        msgs.append("row-0 col keys have zero values (all must be non-zero)")
    # Col 0 row keys (rows 1+) must all be non-zero
    if any(grid[r][0] == 0 for r in range(1, h)):
        msgs.append("col-0 row keys have zero values (all must be non-zero)")
    # (0,0) must be zero
    if grid[0][0] != 0:
        msgs.append(f"corner (0,0) must be 0, found {grid[0][0]}")
    all_keys = [grid[0][c] for c in range(1, w)] + [grid[r][0] for r in range(1, h)]
    if len(set(all_keys)) < 2:
        msgs.append("all row/col keys are the same color: checkerboard alternation is hidden")
    # Interior body (rows 1+, cols 1+) must be all-zero
    nonzero_body = [(r, c) for r in range(1, h) for c in range(1, w) if grid[r][c] != 0]
    if nonzero_body:
        msgs.append(f"interior body has {len(nonzero_body)} non-zero cells (should be blank before rule fills)")
    return msgs
